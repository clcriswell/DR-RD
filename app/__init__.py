from app.logging_setup import init_gcp_logging
import os, re
import json
import logging
import streamlit as st
import openai
from agents import initialize_agents
from agents.synthesizer import compose_final_proposal
from memory.memory_manager import MemoryManager
from memory import audit_logger  # import the audit logger
from collaboration import agent_chat
from utils.refinement import refine_agent_output
from agents.simulation_agent import SimulationAgent
import uuid
import io
import fitz
import time
from markdown_pdf import MarkdownPdf, Section
from dr_rd.config.feature_flags import (
    get_env_defaults,
    EVAL_THRESHOLD,
    COVERAGE_THRESHOLD,
    MAX_LAPS,
    RUN_SOFT_TIME_LIMIT_SEC,
    AGENT_HRM_ENABLED,
    AGENT_TOPK,
    AGENT_MAX_RETRIES,
    AGENT_THRESHOLD,
)
from dr_rd.config.mode_profiles import apply_profile, UI_PRESETS
from dr_rd.hrm_engine import HRMLoop
from dr_rd.hrm_bridge import HRMBridge
from dr_rd.agents.hrm_agent import HRMAgent
from dr_rd.evaluators import feasibility_ev, clarity_ev, coherence_ev, goal_fit_ev
from dr_rd.utils.firestore_workspace import FirestoreWorkspace as WS
from dr_rd.utils.model_router import pick_model, difficulty_from_signals, CallHints
from dr_rd.utils.llm_client import llm_call, METER
from app.ui_cost_meter import render_cost_summary, render_estimator


live_tokens = None
live_cost = None


def update_cost(price_per_1k: float = 0.005):
    global live_tokens, live_cost
    if live_tokens is None or live_cost is None:
        return
    t = METER.total()
    live_tokens.metric("Tokens used", f"{t:,}")
    live_cost.metric("Cost so far", f"${t/1000*price_per_1k:,.4f}")

WRAP_CSS = """
pre, code {
    white-space: pre-wrap;
    word-break: break-word;
    overflow-wrap: anywhere;
}
"""


cache_resource = getattr(st, "cache_resource", lambda func: func)


@cache_resource
def setup_logging():
    """Initialize Google Cloud logging once per session."""
    init_gcp_logging()
    return True


@cache_resource
def get_agents():
    """Create and return the initialized agents."""
    return initialize_agents()


@cache_resource
def get_memory_manager():
    """Return a cached instance of the memory manager."""
    return MemoryManager()


def generate_pdf(markdown_text):
    if isinstance(markdown_text, dict):
        markdown_text = markdown_text.get("document", "")
    pdf = MarkdownPdf(toc_level=2)
    pdf.add_section(Section(markdown_text), user_css=WRAP_CSS)
    pdf.writer.close()
    pdf.out_file.seek(0)
    try:
        doc = fitz.Story.add_pdf_links(pdf.out_file, pdf.hrefs)
    except Exception as e:
        logging.warning(f"Failed to add PDF links: {e}")
        pdf.out_file.seek(0)
        doc = fitz.open(stream=pdf.out_file, filetype="pdf")
    doc.set_metadata(pdf.meta)
    if pdf.toc_level > 0:
        doc.set_toc(pdf.toc)
    buffer = io.BytesIO()
    if pdf.optimize:
        doc.ez_save(buffer)
    else:
        doc.save(buffer)
    doc.close()
    buffer.seek(0)
    return buffer.read()


def safe_log_step(project_id, role, step_type, content, success=True):
    """Safely log audit steps without crashing the app."""
    try:
        audit_logger.log_step(project_id, role, step_type, content, success=success)
    except Exception as e:
        logging.warning(f"Audit logging failed: {e}")


def merge_brief(brief, advice_list):
    brief = dict(brief or {})
    existing = list(brief.get("help_notes") or [])
    if advice_list:
        existing.extend(advice_list if isinstance(advice_list, list) else [advice_list])
    brief["help_notes"] = existing
    return brief


def extract_json_from_markdown(md: str):
    """Extract JSON array from a markdown code block."""
    match = re.search(r"```json\s*(\[.*?\])\s*```", md, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return []
    return []


def strip_json_block(md: str) -> str:
    """Remove JSON code block from markdown output."""
    return re.sub(r"```json\s*.*?\s*```", "", md, flags=re.DOTALL).strip()


def _get_qs_flag(name: str) -> bool:
    try:
        qs = st.query_params if hasattr(st, "query_params") else st.experimental_get_query_params()
        v = qs.get(name, ["0"])
        return (v if isinstance(v, list) else [v])[0] in ("1", "true", "True")
    except Exception:
        return False


def _set_qs_flag(name: str, on: bool):
    try:
        # Streamlit new API:
        if hasattr(st, "query_params"):
            qp = dict(st.query_params)
            qp[name] = "1" if on else "0"
            st.query_params.clear()
            st.query_params.update(qp)
        else:
            st.experimental_set_query_params(
                **{**st.experimental_get_query_params(), name: "1" if on else "0"}
            )
    except Exception:
        pass


def maybe_init_gcp_logging() -> bool:
    """Initialise GCP logging once if credentials are available.

    Returns ``True`` if logging was initialised, otherwise ``False``. The
    result is cached in ``st.session_state`` to avoid repeated attempts on
    Streamlit reruns.
    """

    # If we've already attempted initialisation, return the cached result
    if "gcp_logging_initialized" in st.session_state:
        return st.session_state["gcp_logging_initialized"]

    # Check that required secrets are present before calling init_gcp_logging
    creds = st.secrets.get("gcp_service_account", {})
    if creds.get("private_key"):
        st.session_state["gcp_logging_initialized"] = init_gcp_logging()
    else:
        logging.info("GCP logging disabled: missing gcp_service_account credentials")
        st.session_state["gcp_logging_initialized"] = False

    return st.session_state["gcp_logging_initialized"]


def _slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s[:64] or "project"


def get_project_id() -> str:
    """Prefer a slug of the Project Name; fallback to UUID on first run."""
    pname = st.session_state.get("project_name")
    if pname:
        return _slugify(pname)
    if "project_id" not in st.session_state:
        st.session_state["project_id"] = str(uuid.uuid4())
    return st.session_state["project_id"]


def run_manual_pipeline(
    agents,
    memory_manager,
    similar_ideas,
    idea,
    refinement_rounds,
    simulate_enabled,
    design_depth,
    re_run_simulations,
):
    logging.info(
        f"Running domain experts with refinement_rounds={refinement_rounds}, "
        f"design_depth={design_depth}, simulate_enabled={simulate_enabled}"
    )
    answers = {}
    prev_outputs = []
    simulation_agent = SimulationAgent() if simulate_enabled else None

    # Initial execution by all expert agents
    for role, task in st.session_state["plan"].items():
        agent = agents.get(role)
        if not agent:
            st.warning(f"No agent registered for role: {role}")
            continue
        logging.info(f"Executing agent {role} with task: {task}")
        with st.spinner(f"🤖 {role} working..."):
            try:
                memory_context = (
                    memory_manager.get_project_summaries(similar_ideas)
                    if similar_ideas
                    else ""
                )
                prompt_base = agent.user_prompt_template.format(idea=idea, task=task)
                depth = design_depth.capitalize()
                if depth == "High":
                    prompt_base += "\n\n**Design Depth: High** – Include all relevant component-level details, diagrams, and trade-off analysis."
                elif depth == "Low":
                    prompt_base += "\n\n**Design Depth: Low** – Provide only a high-level summary with minimal detail."
                else:
                    prompt_base += "\n\n**Design Depth: Medium** – Provide a moderate level of detail with key diagrams and justifications."
                previous = "\n\n".join(prev_outputs)
                prompt_parts = [memory_context, previous, prompt_base]
                prompt_with_context = "\n\n".join([p for p in prompt_parts if p])
                diff = st.session_state.get("difficulty", "normal")
                sel = pick_model(CallHints(stage="exec", difficulty=diff))
                logging.info(f"Model[exec]={sel['model']} params={sel['params']}")
                response = llm_call(
                    openai,
                    sel["model"],
                    stage="exec",
                    messages=[
                        {"role": "system", "content": agent.system_message},
                        {"role": "user", "content": prompt_with_context},
                    ],
                    **sel["params"],
                )
                result = response.choices[0].message.content.strip()
                update_cost()
            except Exception as e:
                result = f"❌ {role} failed: {e}"
        # If simulations are enabled, run simulation and potentially refine output
        if simulate_enabled and result and not result.startswith("❌"):
            # Determine simulation type via SimulationAgent logic and run simulation
            if "engineer" in role.lower():
                sim_type = "structural"
            elif "cto" in role.lower():
                sim_type = "electronics"
            elif "research scientist" in role.lower():
                sim_type = (
                    "chemical"
                    if any(
                        term in result.lower()
                        for term in [
                            "chemical",
                            "chemistry",
                            "compound",
                            "reaction",
                            "material",
                        ]
                    )
                    else "thermal"
                )
            else:
                sim_type = ""
            if sim_type:
                logging.info(f"Running {sim_type} simulation for role {role}")
                sim_metrics = simulation_agent.sim_manager.simulate(sim_type, result)
            else:
                logging.info(f"No simulation available for role {role}; skipping.")
                sim_metrics = {"pass": True, "failed": []}
            score = 1.0 if sim_metrics.get("pass", True) else 0.0
            coverage = 1.0
            st.session_state["difficulty"] = difficulty_from_signals(score, coverage)
            # Check simulation results
            if not sim_metrics.get("pass", True):
                # Log initial output failure
                failed_list = sim_metrics.get("failed", [])
                fail_desc = ", ".join(failed_list) if failed_list else "criteria"
                safe_log_step(
                    get_project_id(),
                    role,
                    "Output",
                    f"Failed {fail_desc}",
                    success=False,
                )
                # Attempt up to 2 refinements based on failed criteria
                for attempt in range(
                    1, 3
                ):  # attempt = 1 for first retry, 2 for second retry
                    # Prepare feedback context with failed criteria
                    feedback = ""
                    if failed_list:
                        feedback = f"The simulation indicates failure in: {', '.join(failed_list)}. Please address these issues in the design."
                    # Construct messages to re-run agent with feedback
                    try:
                        sel = pick_model(CallHints(stage="exec", difficulty="hard"))
                        logging.info(
                            f"Model[exec]={sel['model']} params={sel['params']}"
                        )
                        revised_response = llm_call(
                            openai,
                            sel["model"],
                            stage="exec",
                            messages=[
                                {"role": "system", "content": agent.system_message},
                                {
                                    "role": "user",
                                    "content": agent.user_prompt_template.format(
                                        idea=idea, task=task
                                    ),
                                },
                                {"role": "assistant", "content": result},
                                {
                                    "role": "user",
                                    "content": (
                                        feedback
                                        if feedback
                                        else "The design did not meet some requirements; please refine the proposal."
                                    ),
                                },
                            ],
                            **sel["params"],
                        )
                        update_cost()
                        new_result = revised_response.choices[0].message.content.strip()
                    except Exception as e:
                        new_result = result  # if the re-run fails, keep the last result
                    # Run simulation again on the revised output
                    new_metrics = simulation_agent.sim_manager.simulate(
                        sim_type, new_result
                    )
                    if new_metrics.get("pass", True):
                        # Success on retry
                        result = new_result
                        # Log successful retry attempt
                        safe_log_step(
                            get_project_id(),
                            role,
                            f"Retry {attempt}",
                            "Passed Simulation",
                            success=True,
                        )
                        # Format simulation results for output if showing immediately
                        if refinement_rounds == 1:
                            sim_text = simulation_agent.run_simulation(role, result)
                            if sim_text:
                                result = f"{new_result}\n\n{sim_text}"
                        break
                    else:
                        # Still failing after this attempt
                        failed_list = new_metrics.get("failed", [])
                        fail_desc = (
                            ", ".join(failed_list) if failed_list else "criteria"
                        )
                        result = new_result  # update result to the latest attempt for potential display
                        # Log the failed retry attempt
                        safe_log_step(
                            get_project_id(),
                            role,
                            f"Retry {attempt}",
                            f"Failed {fail_desc}",
                            success=False,
                        )
                        if attempt == 2:
                            # After 2 retries (total 3 attempts including initial) still failing
                            getattr(
                                st,
                                "error",
                                lambda *a, **k: None,
                            )(
                                f"{role} could not meet simulation constraints after 2 attempts. Halting execution."
                            )
                            # Log halting scenario
                            safe_log_step(
                                get_project_id(),
                                role,
                                "Abort",
                                "Simulation constraints unmet after 2 retries",
                                success=False,
                            )
                            st.stop()
            else:
                # Simulation passed on first try
                safe_log_step(
                    get_project_id(), role, "Output", "Passed Simulation", success=True
                )
                # Append simulation metrics to the output if no further refinement rounds
                if refinement_rounds == 1:
                    sim_text = simulation_agent.run_simulation(role, result)
                    if sim_text:
                        result = f"{result}\n\n{sim_text}"
        else:
            # Simulations not enabled or result is an error
            # Log the output as completed (success=True by default if no simulation)
            if not result.startswith("❌"):
                safe_log_step(
                    get_project_id(), role, "Output", "Completed", success=True
                )
            else:
                safe_log_step(
                    get_project_id(),
                    role,
                    "Output",
                    "Failed to generate",
                    success=False,
                )

        answers[role] = result
        prev_outputs.append(strip_json_block(result))

        # Display initial outputs immediately if no refinement rounds selected
        if refinement_rounds == 1:
            st.markdown("---")
            st.markdown(f"### {role}")
            st.markdown(result, unsafe_allow_html=True)
    # Save initial answers
    st.session_state["answers"] = answers

    # Agent-to-Agent collaboration after initial outputs (CTO ↔ Research Scientist)
    if "CTO" in answers and "Research Scientist" in answers:
        with st.spinner("🔄 CTO and Research Scientist collaborating..."):
            try:
                updated_cto, updated_rs = agent_chat(
                    agents["CTO"],
                    agents["Research Scientist"],
                    idea,
                    answers["CTO"],
                    answers["Research Scientist"],
                )
                answers["CTO"] = updated_cto
                answers["Research Scientist"] = updated_rs
                # Display revised outputs if no further refinement rounds
                if refinement_rounds == 1:
                    st.markdown("---")
                    st.markdown("### CTO (Revised after collaboration)")
                    if simulate_enabled:
                        sim_cto = simulation_agent.run_simulation("CTO", updated_cto)
                        if sim_cto:
                            updated_cto = f"{updated_cto}\n\n{sim_cto}"
                            answers["CTO"] = updated_cto
                    st.markdown(updated_cto, unsafe_allow_html=True)
                    st.markdown("---")
                    st.markdown("### Research Scientist (Revised after collaboration)")
                    if simulate_enabled:
                        sim_rs = simulation_agent.run_simulation(
                            "Research Scientist", updated_rs
                        )
                        if sim_rs:
                            updated_rs = f"{updated_rs}\n\n{sim_rs}"
                            answers["Research Scientist"] = updated_rs
                    st.markdown(updated_rs, unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"Agent collaboration failed: {e}")
        # Update session state with collaborated outputs
        st.session_state["answers"] = answers
        if use_firestore:
            try:
                doc_id = get_project_id()
                db.collection("dr_rd_projects").document(doc_id).set(
                    {"outputs": st.session_state["answers"], **st.session_state.get("test_marker", {})},
                    merge=True,
                )
            except Exception as e:
                logging.error(f"Save outputs failed: {e}")

    # Iterative refinement rounds if selected
    if refinement_rounds > 1:
        for r in range(2, refinement_rounds + 1):
            st.info(f"Refinement round {r-1} of {refinement_rounds-1}...")
            new_answers = {}
            for role, task in st.session_state["plan"].items():
                agent = agents.get(role)
                if not agent:
                    continue
                with st.spinner(f"🤖 Refining {role}'s output..."):
                    try:
                        other_outputs = {
                            other_role: ans
                            for other_role, ans in answers.items()
                            if other_role != role
                        }
                        refined_output = refine_agent_output(
                            agent, idea, task, answers.get(role, ""), other_outputs
                        )
                        update_cost()
                    except Exception as e:
                        refined_output = f"❌ {role} refinement failed: {e}"
                new_answers[role] = refined_output
            answers = new_answers
        # After all refinement rounds, append simulation results if enabled (re-run simulations for final outputs)
        if simulate_enabled:
            for role, output in answers.items():
                sim_text = (
                    SimulationAgent().run_simulation(role, output)
                    if re_run_simulations or True
                    else ""
                )
                # Note: We always run final simulation if enabled to display up-to-date metrics
                if sim_text:
                    answers[role] = f"{output}\n\n{sim_text}"
        # Display final expert outputs after refinements
        st.subheader("Final Expert Outputs after Refinement")
        for role, output in answers.items():
            st.markdown("---")
            st.markdown(f"### {role} (Refined)")
            st.markdown(output, unsafe_allow_html=True)
        st.session_state["answers"] = answers
        if use_firestore:
            try:
                doc_id = get_project_id()
                db.collection("dr_rd_projects").document(doc_id).set(
                    {"outputs": st.session_state["answers"], **st.session_state.get("test_marker", {})},
                    merge=True,
                )
            except Exception as e:
                logging.error(f"Save outputs failed: {e}")


def main():
    maybe_init_gcp_logging()
    project_id = get_project_id()
    use_firestore = False
    try:
        from google.cloud import firestore
        from google.oauth2 import service_account

        sa_info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(sa_info)
        gcp_project = sa_info.get("project_id")
        db = firestore.Client(credentials=credentials, project=gcp_project)
        ws = WS(project_id)
        try:
            slug_id = _slugify(st.session_state.get("project_name", ""))
            if slug_id:
                old_id = project_id
                if old_id != slug_id:
                    try:
                        old_doc = db.collection("dr_rd_projects").document(old_id).get()
                        if old_doc.exists:
                            db.collection("dr_rd_projects").document(slug_id).set(
                                {**old_doc.to_dict(), **st.session_state.get("test_marker", {})},
                                merge=True,
                            )
                    except Exception:
                        pass
                st.session_state["project_id"] = slug_id
                ws = WS(slug_id)
        except Exception as _e:
            pass
        use_firestore = True
    except Exception as e:  # pragma: no cover - optional dependency
        logging.info(f"Firestore disabled: {e}")
        class _DummyWS:
            def log(self, msg: str) -> None:  # pragma: no cover - simple stub
                logging.debug(msg)

        ws = _DummyWS()

    base_agents = get_agents()
    agents = dict(base_agents)
    if AGENT_HRM_ENABLED and use_firestore:
        planner = agents.get("Planner")
        synth = agents.get("Synthesizer")
        agents["Planner"] = HRMAgent(
            planner,
            [feasibility_ev, clarity_ev],
            ws,
            "Planner",
            top_k=AGENT_TOPK,
            max_retries=AGENT_MAX_RETRIES,
            threshold=AGENT_THRESHOLD,
        )
        agents["Synthesizer"] = HRMAgent(
            synth,
            [coherence_ev, goal_fit_ev],
            ws,
            "Synthesizer",
            top_k=AGENT_TOPK,
            max_retries=AGENT_MAX_RETRIES,
            threshold=AGENT_THRESHOLD,
        )

    memory_manager = get_memory_manager()

    st.set_page_config(page_title="Dr. R&D", layout="wide")
    st.title("Dr. R&D")

    global live_tokens, live_cost
    sidebar_root = getattr(st, "sidebar", st)

    def _placeholder():  # pragma: no cover - simple sidebar stub
        class _P:
            def metric(self, *args, **kwargs):
                pass

        return _P()

    empty_fn = getattr(sidebar_root, "empty", _placeholder)
    live_tokens = empty_fn()
    live_cost = empty_fn()

    sidebar = getattr(st, "sidebar", st)
    if hasattr(sidebar, "title"):
        sidebar.title("Configuration")
    else:
        st.markdown("## Configuration")

    developer_expander = getattr(sidebar, "expander", None)
    if callable(developer_expander):
        with developer_expander("Developer", expanded=False):
            if "dev_mode" not in st.session_state:
                st.session_state["dev_mode"] = _get_qs_flag("dev")
            toggle_fn = getattr(st, "toggle", getattr(st, "checkbox", lambda *a, **k: False))
            dev_on = toggle_fn(
                "Enable Test (dev) mode",
                value=bool(st.session_state.get("dev_mode")),
                help="Adds a low-cost end-to-end test mode.",
            )
            st.session_state["dev_mode"] = dev_on
            _set_qs_flag("dev", dev_on)
    else:
        if "dev_mode" not in st.session_state:
            st.session_state["dev_mode"] = _get_qs_flag("dev")

    mode_label_to_key = {"Fast": "fast", "Balanced": "balanced", "Deep": "deep"}
    if st.session_state.get("dev_mode"):
        mode_label_to_key["Test (dev)"] = "test"
    mode_container = sidebar if hasattr(sidebar, "radio") else st
    labels = list(mode_label_to_key.keys())
    if hasattr(mode_container, "radio"):
        default_index = labels.index("Balanced") if "Balanced" in labels else 0
        selected_label = mode_container.radio("Run Mode", labels, index=default_index)
    else:  # fallback for test stubs
        selected_label = "Balanced"
    selected_mode = mode_label_to_key[selected_label]
    if selected_mode == "test":
        st.info(
            "**Test (dev)** is ON: minimal tokens, capped domains, tiny image, truncated outputs."
        )
    env_defaults = get_env_defaults()
    final_flags = apply_profile(env_defaults, selected_mode, overrides=None)
    st.session_state["final_flags"] = final_flags
    import config.feature_flags as ff
    for k, v in final_flags.items():
        setattr(ff, k, v)
    ui_preset = UI_PRESETS[selected_mode]
    st.session_state["simulate_enabled"] = ui_preset["simulate_enabled"]
    st.session_state["design_depth"] = ui_preset["design_depth"]
    st.session_state["test_marker"] = {"test": True} if final_flags.get("TEST_MODE") else {}
    if hasattr(st, "caption"):
        st.caption(
            ("**DEV** • " if selected_mode == "test" else "")
            + f"Mode: {selected_label} • Depth={ui_preset['design_depth']} • "
            + f"Refinement rounds={ui_preset['refinement_rounds']} • "
            + f"Simulations={'on' if ui_preset['simulate_enabled'] else 'off'}"
        )
    project_names = []
    project_doc_ids = {}
    if use_firestore:
        try:
            docs = db.collection("dr_rd_projects").stream()
            for doc in docs:
                data = doc.to_dict() or {}
                name = data.get("name") or doc.id
                project_doc_ids[name] = doc.id
            project_names = list(project_doc_ids.keys())
        except Exception as e:  # pragma: no cover - external service
            logging.error(f"Could not fetch projects from Firestore: {e}")
    if not use_firestore:
        project_names = [
            entry.get("name", "(unnamed)") for entry in memory_manager.data
        ]

    current_project = st.session_state.get("project_name")
    if current_project and current_project not in project_names:
        project_names.append(current_project)

    selected_index = 0
    if (
        "project_name" in st.session_state
        and st.session_state["project_name"] in project_names
    ):
        selected_index = project_names.index(st.session_state["project_name"]) + 1
    selectbox_container = sidebar if hasattr(sidebar, "selectbox") else st
    selected_project = selectbox_container.selectbox(
        "🔄 Load Saved Project",
        ["(New Project)"] + project_names,
        index=selected_index,
    )

    last_selected = st.session_state.get("last_selected_project")
    if selected_project != last_selected:
        st.session_state.pop("hrm_report", None)
        st.session_state.pop("hrm_state", None)
        if selected_project != "(New Project)":
            if use_firestore:
                try:
                    doc_id = project_doc_ids.get(selected_project, selected_project)
                    doc = db.collection("dr_rd_projects").document(doc_id).get()
                    if doc.exists:
                        data = doc.to_dict() or {}
                        st.session_state["idea"] = data.get("idea", "")
                        st.session_state["plan"] = data.get("plan", {})
                        st.session_state["answers"] = data.get("outputs", {})
                        st.session_state["final_doc"] = data.get("proposal", "")
                        st.session_state["images"] = data.get("images", [])
                        st.session_state["project_name"] = data.get(
                            "name", selected_project
                        )
                except Exception as e:  # pragma: no cover - external service
                    logging.error(f"Could not load project from Firestore: {e}")
            else:
                for entry in memory_manager.data:
                    if entry.get("name") == selected_project:
                        st.session_state["idea"] = entry.get("idea", "")
                        st.session_state["plan"] = entry.get("plan", {})
                        st.session_state["answers"] = entry.get("outputs", {})
                        st.session_state["final_doc"] = entry.get("proposal", "")
                        st.session_state["images"] = entry.get("images", [])
                        st.session_state["project_name"] = entry.get(
                            "name", selected_project
                        )
                        break
        else:
            for key in [
                "idea",
                "plan",
                "answers",
                "final_doc",
                "images",
                "project_name",
                "project_id",
                "hrm_report",
                "hrm_state",
            ]:
                st.session_state.pop(key, None)
        st.session_state["last_selected_project"] = selected_project
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()

    project_name = st.text_input(
        "🏷️ Project Name:", value=st.session_state.get("project_name", "")
    )
    idea = st.text_input(
        "🧠 Enter your project idea:", value=st.session_state.get("idea", "")
    )
    if not idea:
        st.info("Please describe an idea to get started.")
        st.stop()
    if not project_name:
        st.info("Please provide a project name to get started.")
        st.stop()
    st.session_state["project_name"] = project_name

    similar_ideas = memory_manager.find_similar_ideas(idea)
    if similar_ideas:
        st.info("Found similar past projects: " + ", ".join(similar_ideas))

    render_estimator(
        selected_mode, st.session_state.get("idea", ""), price_per_1k=0.005
    )

    if st.button("1⃣ Generate Research Plan"):
        logging.info(f"User generated plan for idea: {idea}")
        try:
            with st.spinner("📝 Planning..."):
                try:
                    raw_plan = agents["Planner"].run(
                        idea,
                        "Break down the project into role-specific tasks",
                        difficulty=st.session_state.get("difficulty", "normal"),
                    )
                except TypeError:
                    raw_plan = agents["Planner"].run(
                        idea,
                        "Break down the project into role-specific tasks",
                    )
                update_cost()
                if not isinstance(raw_plan, dict):
                    getattr(
                        st, "error", lambda *a, **k: None
                    )(
                        "Plan generation failed – received an unexpected response format."
                    )
                    st.stop()
                plan = {role: task for role, task in raw_plan.items() if role in agents}
                dropped = [r for r in raw_plan if r not in agents]
                if dropped:
                    st.warning(f"Dropped unrecognized roles: {', '.join(dropped)}")
            st.session_state["plan"] = plan
            safe_log_step(
                get_project_id(),
                "Planner",
                "Output",
                "Plan generated",
                success=True,
            )
            if use_firestore:
                try:
                    doc_id = get_project_id()
                    db.collection("dr_rd_projects").document(doc_id).set(
                        {
                            "name": st.session_state.get("project_name", ""),
                            "idea": idea,
                            "plan": st.session_state["plan"],
                            **st.session_state.get("test_marker", {}),
                        },
                        merge=True,
                    )
                except Exception as e:
                    logging.error(f"Save plan failed: {e}")
            render_cost_summary(selected_mode, st.session_state.get("plan"))
        except openai.OpenAIError as e:
            logging.exception("OpenAI error during plan generation: %s", e)
            getattr(
                st,
                "error",
                lambda *a, **k: None,
            )(
                "Planning failed: Unable to generate plan. Please check your API key or try again later."
            )
            st.write("Plan generation failed:", e)
        except Exception as e:  # pylint: disable=broad-except
            logging.exception("Unexpected error during plan generation: %s", e)
            getattr(st, "error", lambda *a, **k: None)(
                "Planning failed: An unexpected error occurred."
            )
            st.write("Plan generation failed:", e)

    if "plan" in st.session_state:
        st.subheader("Project Plan (Role → Task)")
        st.json(st.session_state["plan"])

        refinement_rounds = ui_preset["refinement_rounds"]
        simulate_enabled = st.session_state.get("simulate_enabled", True)
        design_depth = st.session_state.get("design_depth", "Low")
        re_run_simulations = ui_preset["rerun_sims_each_round"]

        def classic_execute(tasks):
            outputs = {}
            for t in tasks:
                agent = agents.get(t.get("role"))
                if not agent:
                    continue
                outputs[t["role"]] = agent.run(idea, t.get("task", ""))
            render_cost_summary(selected_mode, st.session_state.get("plan"))
            return outputs

        if st.button("2⃣ Run All Domain Experts"):
            brief = {"idea": idea}
            hrm = HRMBridge(HRMLoop, ws)
            with st.spinner("🤖 Running plan → execute → evaluate…"):
                t0 = time.time()
                tasks = [
                    {"role": r, "task": t}
                    for r, t in st.session_state.get("plan", {}).items()
                ]
                if not tasks:
                    tasks = hrm.plan_only(brief)
                results = {t["role"]: "out" for t in tasks}
                score, notes, cov = hrm.evaluate_only(results)
                laps = 0
                while (score < EVAL_THRESHOLD or cov < COVERAGE_THRESHOLD) and laps < MAX_LAPS:
                    if time.time() - t0 > RUN_SOFT_TIME_LIMIT_SEC:
                        ws.log("⏱ Soft time limit reached; skipping extra lap")
                        break
                    advice = hrm.seek_help_only(brief, results)
                    brief = merge_brief(brief, advice)
                    tasks = hrm.plan_only(brief, replan=True)
                    results = classic_execute(tasks)
                    score, notes, cov = hrm.evaluate_only(results)
                    laps += 1
                final_report = agents["Synthesizer"].run(idea, results)
                ws.log(f"✅ Final score={score:.2f}")
            st.session_state["hrm_report"] = final_report
            st.session_state["hrm_state"] = {"results": results}
            st.session_state["answers"] = {
                r: "out" for r in st.session_state.get("plan", {})
            }
            if use_firestore:
                try:
                    doc_id = get_project_id()
                    db.collection("dr_rd_projects").document(doc_id).set(
                        {"outputs": st.session_state["answers"], **st.session_state.get("test_marker", {})},
                        merge=True,
                    )
                except Exception as e:
                    logging.error(f"Save outputs failed: {e}")
            render_cost_summary(selected_mode, st.session_state.get("plan"))
            getattr(
                st, "success", lambda *a, **k: None
            )("✅ HRM R&D complete!")

    if st.session_state.get("hrm_report"):
        st.subheader("Final Report")
        st.markdown(st.session_state["hrm_report"])
        pdf = generate_pdf(st.session_state["hrm_report"])
        getattr(
            st, "download_button", lambda *a, **k: None
        )(
            "📄 Download Report",
            data=pdf,
            file_name="R&D_Report.pdf",
            mime="application/pdf",
        )
        st.subheader("Results")
        st.json(st.session_state.get("hrm_state", {}).get("results", {}))

    if "answers" in st.session_state:
        st.subheader("Domain Expert Outputs")
        expander_container = st if hasattr(st, "expander") else sidebar
        for role, output in st.session_state["answers"].items():
            with expander_container.expander(role, expanded=False):
                st.markdown(output, unsafe_allow_html=True)
                suggestion = st.text_input(
                    f"💡 Suggest an edit for {role}:",
                    key=f"suggestion_{role.replace(' ', '_')}",
                )
                try:
                    submit_clicked = st.button(
                        "Submit Suggestion", key=f"submit_{role.replace(' ', '_')}"
                    )
                except TypeError:  # pragma: no cover - for simple stubs in tests
                    submit_clicked = st.button("Submit Suggestion")

                if submit_clicked:
                    try:
                        planner_agent = agents.get("Planner")
                        domain_agent = agents.get(role)
                        orig_output = output
                        role_task = st.session_state["plan"].get(role, "")
                        planner_query = (
                            f"For the project idea '{idea}', the user suggests: '{suggestion}' for the {role}'s output. "
                            f"Given the {role}'s task '{role_task}', should this suggestion be incorporated to improve the overall plan? "
                            "Respond with Yes or No and a brief reason."
                        )
                        sel = pick_model(CallHints(stage="plan"))
                        logging.info(
                            f"Model[plan]={sel['model']} params={sel['params']}"
                        )
                        planner_resp = llm_call(
                            openai,
                            sel["model"],
                            stage="plan",
                            messages=[
                                {
                                    "role": "system",
                                    "content": planner_agent.system_message,
                                },
                                {"role": "user", "content": planner_query},
                            ],
                            **sel["params"],
                        )
                        update_cost()
                        planner_text = planner_resp.choices[0].message.content.strip()
                        integrate = planner_text.lower().startswith("yes")
                        planner_reason = (
                            planner_text[3:].strip(" .:-")
                            if integrate
                            else planner_text[2:].strip(" .:-")
                        )

                        if integrate:
                            suggestion_prompt = (
                                f"The Planner approved this suggestion: {planner_reason}. "
                                "Please update your output accordingly. First, provide the revised output in detail, "
                                "then explain briefly how this change improves the design."
                            )
                        else:
                            suggestion_prompt = (
                                f"The Planner advises against this suggestion: {planner_reason}. "
                                "Explain to the user why this suggestion won't be adopted."
                            )
                        sel = pick_model(CallHints(stage="exec"))
                        logging.info(
                            f"Model[exec]={sel['model']} params={sel['params']}"
                        )
                        revised_resp = llm_call(
                            openai,
                            sel["model"],
                            stage="exec",
                            messages=[
                                {
                                    "role": "system",
                                    "content": domain_agent.system_message,
                                },
                                {
                                    "role": "user",
                                    "content": domain_agent.user_prompt_template.format(
                                        idea=idea, task=role_task
                                    ),
                                },
                                {"role": "assistant", "content": orig_output},
                                {"role": "user", "content": suggestion_prompt},
                            ],
                            **sel["params"],
                        )
                        update_cost()
                        revised_output = revised_resp.choices[0].message.content.strip()
                        st.markdown(
                            f"**{role} response:**\n\n{revised_output}",
                            unsafe_allow_html=True,
                        )
                        if integrate:
                            try:
                                accept = st.button(
                                    "✅ Accept Revision",
                                    key=f"accept_{role.replace(' ', '_')}",
                                )
                                continue_discussion = st.button(
                                    "🗨️ Continue Discussion",
                                    key=f"continue_{role.replace(' ', '_')}",
                                )
                            except TypeError:  # pragma: no cover - test stubs
                                accept = st.button("✅ Accept Revision")
                                continue_discussion = st.button("🗨️ Continue Discussion")
                            if accept:
                                parts = revised_output.strip().rsplit("\n\n", 1)
                                updated_output_text = (
                                    parts[0] if len(parts) >= 1 else revised_output
                                )
                                st.session_state["answers"][role] = updated_output_text
                                getattr(
                                    st, "success", lambda *a, **k: None
                                )(
                                    f"Accepted revision for {role}. The output has been updated."
                                )
                            if continue_discussion:
                                st.info(
                                    f"You can refine your suggestion for {role} and submit again."
                                )
                    except Exception as e:  # pylint: disable=broad-except
                        getattr(
                            st, "error", lambda *a, **k: None
                        )(f"Failed to process suggestion for {role}: {e}")

        if st.button("3⃣ Compile Final Proposal"):
            logging.info("User compiled final proposal")
            with st.spinner("🚀 Synthesizing final R&D proposal..."):
                try:
                    result = compose_final_proposal(
                        idea,
                        st.session_state["answers"],
                        include_simulations=st.session_state.get(
                            "simulate_enabled", True
                        ),
                    )
                    if isinstance(result, dict) and "document" in result:
                        final_doc = result["document"]
                        st.session_state["images"] = result.get("images", [])
                    else:
                        final_doc = result
                        st.session_state["images"] = []
                    update_cost()
                    bom = []
                    for output in st.session_state["answers"].values():
                        bom.extend(extract_json_from_markdown(output))
                    if bom:
                        bom_md = "|Component|Quantity|Specs|\n|---|---|---|\n"
                        incomplete_items = []
                        for item in bom:
                            name = item.get("name")
                            quantity = item.get("quantity")
                            specs = item.get("specs")
                            if None in (name, quantity, specs):
                                logging.warning(
                                    f"Skipping incomplete BOM entry: {item}"
                                )
                                incomplete_items.append(item)
                                continue
                            bom_md += f"|{name}|{quantity}|{specs}|\n"
                        if incomplete_items:
                            st.warning(
                                f"Skipped incomplete BOM entries: {incomplete_items}"
                            )
                        final_doc = final_doc.replace(
                            "## Bill of Materials\n",
                            f"## Bill of Materials\n\n{bom_md}\n",
                        )
                    memory_manager.store_project(
                        st.session_state.get("project_name", ""),
                        idea,
                        st.session_state.get("plan", {}),
                        st.session_state["answers"],
                        final_doc,
                        st.session_state.get("images", []),
                    )
                except Exception as e:  # pylint: disable=broad-except
                    getattr(
                        st, "error", lambda *a, **k: None
                    )(f"Final proposal synthesis failed: {e}")
                    logging.exception("Error during final proposal synthesis: %s", e)
                    st.stop()
            st.session_state["final_doc"] = final_doc
            if use_firestore:
                try:
                    doc_id = get_project_id()
                    db.collection("dr_rd_projects").document(doc_id).set(
                        {"proposal": st.session_state["final_doc"], **st.session_state.get("test_marker", {})},
                        merge=True,
                    )
                except Exception as e:
                    logging.error(f"Save proposal failed: {e}")
            if use_firestore:
                try:
                    doc_id = get_project_id()
                    db.collection("dr_rd_projects").document(doc_id).set(
                        {"images": st.session_state.get("images", []), **st.session_state.get("test_marker", {})},
                        merge=True,
                    )
                except Exception as e:
                    logging.error(f"Save images failed: {e}")

    if "final_doc" in st.session_state:
        st.subheader("📖 Integrated R&D Proposal")
        st.caption(
            "Visuals are auto-generated for Balanced/Deep modes. They’ll also be saved with your project."
        )
        doc_text = st.session_state["final_doc"]
        if isinstance(doc_text, dict):
            imgs = doc_text.get("images")
            doc_text = doc_text.get("document", "")
        else:
            imgs = st.session_state.get("images")
        st.markdown(doc_text)
        if imgs:
            st.subheader("Schematics & Visuals")
            for im in imgs:
                st.image(im["url"], caption=im.get("caption", ""))
        pdf_bytes = generate_pdf(doc_text)
        if hasattr(st, "download_button"):
            st.download_button(
                label="📄 Download Final Report as PDF",
                data=pdf_bytes,
                file_name="R&D_Report.pdf",
                mime="application/pdf",
            )

        import pandas as pd

        by_stage = METER.by_stage()
        df = pd.DataFrame(
            [
                {"stage": k, "tokens": v, "dollars_est": v / 1000 * 0.005}
                for k, v in by_stage.items()
            ]
        )
        if not df.empty:
            df = df.sort_values("tokens", ascending=False)
            getattr(st, "caption", lambda *a, **k: None)(
                "Token breakdown by stage"
            )
            getattr(st, "dataframe", lambda *a, **k: None)(
                df, use_container_width=True
            )

    st.subheader("💬 Project Chat")
    doc_id = get_project_id()
    prior_chat = []
    if use_firestore:
        try:
            snap = db.collection("dr_rd_projects").document(doc_id).get()
            if snap.exists:
                prior_chat = snap.to_dict().get("chat", []) or []
        except Exception as e:
            logging.error(f"Load chat failed: {e}")
    for m in prior_chat[-30:]:
        role = m.get("role", "assistant")
        content = m.get("content", "")
        getattr(st, "markdown", print)(f"**{role.capitalize()}:** {content}")

    user_msg = getattr(st, "chat_input", lambda *a, **k: None)(
        "Ask a question or propose a refinement…"
    )
    if user_msg:
        context_bits = []
        if st.session_state.get("idea"):
            context_bits.append(f"IDEA: {st.session_state['idea']}")
        if st.session_state.get("plan"):
            context_bits.append(
                f"PLAN ROLES: {', '.join(st.session_state['plan'].keys())}"
            )
        if st.session_state.get("answers"):
            sums = [
                f"{r}: {len((st.session_state['answers'].get(r) or ''))} chars"
                for r in st.session_state["answers"].keys()
            ]
            context_bits.append("OUTPUTS: " + "; ".join(sums))
        if st.session_state.get("final_doc"):
            context_bits.append("PROPOSAL: present")

        from dr_rd.utils.model_router import pick_model, CallHints
        from dr_rd.utils.llm_client import llm_call

        sel = pick_model(CallHints(stage="exec", deep_reasoning=(selected_mode == "deep")))
        msg = "\n\n".join(context_bits) + f"\n\nUser: {user_msg}"
        try:
            reply = llm_call(
                openai,
                sel["model"],
                stage="exec",
                messages=[
                    {
                        "role": "system",
                        "content": "You are the project's on-call R&D assistant.",
                    },
                    {"role": "user", "content": msg},
                ],
                **sel["params"],
            ).choices[0].message.content.strip()
        except Exception as e:
            reply = f"(assistant error: {e})"
        new_chat = prior_chat + [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": reply},
        ]
        if use_firestore:
            try:
                db.collection("dr_rd_projects").document(doc_id).set(
                    {"chat": new_chat, **st.session_state.get("test_marker", {})},
                    merge=True,
                )
            except Exception as e:
                logging.error(f"Save chat failed: {e}")
        getattr(st, "markdown", print)(f"**Assistant:** {reply}")
