import io
import json
import logging
import os
import re
from typing import Dict, List, Optional

import fitz
import openai
import pandas as pd
import streamlit as st
from markdown_pdf import MarkdownPdf, Section
from utils.firestore_workspace import FirestoreWorkspace as WS
from utils.refinement import refine_agent_output

import core
from app.config_loader import load_profile
from app.logging_setup import init_gcp_logging
from app.ui_cost_meter import render_cost_summary
from app.agent_trace_ui import (
    render_agent_trace,
    render_live_status,
    render_exports,
    render_role_summaries,
)
from app.ui_presets import UI_PRESETS
from collaboration import agent_chat
from config.agent_models import AGENT_MODEL_MAP
from config.feature_flags import apply_overrides, get_env_defaults
import config.feature_flags as ff
from core.agents.planner_agent import PlannerAgent
from core.agents.simulation_agent import SimulationAgent
from core.agents.synthesizer_agent import SynthesizerAgent, compose_final_proposal
from core.agents.unified_registry import (
    AGENT_REGISTRY,
    build_agents_unified,
    validate_registry,
)
from core.llm import select_model
from core.llm_client import BUDGET, METER, call_openai, set_budget_manager
from core.model_router import CallHints, difficulty_from_signals, pick_model
from core.orchestrator import execute_plan, generate_plan, run_poc
from core.plan_utils import normalize_plan_to_tasks, normalize_tasks  # noqa: F401
from core.poc.testplan import TestPlan
from core.role_normalizer import group_by_role
from core.role_normalizer import normalize_tasks as normalize_roles_tasks
from core.summarization import two_pass_enabled
from core.summarization.integrator import integrate
from core.summarization.schemas import RoleSummary
from core import tool_router
try:  # optional LangGraph pipeline
    from core.graph import run_langgraph
except Exception:  # pragma: no cover - optional dependency
    run_langgraph = None
try:  # optional AutoGen pipeline
    from core.autogen.run import run_autogen
except Exception:  # pragma: no cover - optional dependency
    run_autogen = None
from dr_rd.core.config_snapshot import build_resolved_config_snapshot
from dr_rd.knowledge.bootstrap import bootstrap_vector_index
from memory import audit_logger  # import the audit logger
from memory.memory_manager import MemoryManager
from pathlib import Path
import tempfile


class _DummyCtx:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False


def _safe_expander(obj, label, expanded=False):
    exp = getattr(obj, "expander", None)
    if callable(exp):
        return exp(label, expanded=expanded)
    return _DummyCtx()


logger = logging.getLogger(__name__)


def _bool_env(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).strip().lower() in {"1", "true", "yes", "on"}


def _str_env(name: str, default: str = "") -> str:
    v = os.getenv(name)
    return default if v is None else str(v).strip()


try:
    from orchestrators.app_builder import build_app_from_idea
except Exception:
    build_app_from_idea = None  # optional feature

try:
    from core.agents.publisher_agent import (
        make_zip_bytes,
        try_create_github_repo,
        write_publishing_md,
    )
    from core.agents.qa_agent import qa_all
except Exception:
    qa_all = None
    make_zip_bytes = write_publishing_md = try_create_github_repo = None


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
    """Create and return the initialized agents using the core registry."""
    mapping = AGENT_MODEL_MAP
    live_backend = _str_env("LIVE_SEARCH_BACKEND").lower()
    base_default = "gpt-4o-mini" if live_backend == "openai" else "gpt-4.1-mini"
    default_model = mapping.get("DEFAULT") or os.getenv("DRRD_OPENAI_MODEL") or base_default
    agents = build_agents_unified(mapping, default_model)
    agents["Planner"] = PlannerAgent(mapping.get("Planner") or default_model)
    agents["Synthesizer"] = SynthesizerAgent(mapping.get("Synthesizer") or default_model)
    logger.info("Registered agents (unified): %s", sorted(agents.keys()))
    return agents


@cache_resource
def get_memory_manager():
    """Return a cached instance of the memory manager."""
    return MemoryManager()


def route_tasks(tasks_any, agents):
    """Normalize ``tasks_any`` and map each task to an agent.

    Unknown roles fall back to the first agent provided.
    """
    tasks = normalize_tasks(normalize_plan_to_tasks(tasks_any))
    if not agents:
        return []
    default_rr, default_agent = next(iter(agents.items()))
    routed = []
    for t in tasks:
        agent = agents.get(t["role"], default_agent)
        rr = t["role"] if t["role"] in agents else default_rr
        routed.append((rr, agent, t))
    return routed


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
    if pdf.toc_level > 0 and pdf.toc:
        try:
            min_level = min(item[0] for item in pdf.toc)
            normalized_toc = [[item[0] - min_level + 1, *item[1:]] for item in pdf.toc]
            doc.set_toc(normalized_toc)
        except Exception as e:
            logging.warning(f"Failed to set PDF ToC: {e}")
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
    if not project_id:
        return
    try:
        audit_logger.log_step(project_id, role, step_type, content, success=success)
    except Exception as e:
        logging.warning(f"Audit logging failed: {e}")


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


def get_project_id() -> Optional[str]:
    """Return a slug of the Project Name if available."""
    pname = st.session_state.get("project_name", "")
    if not pname:
        return None
    return _slugify(pname)


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
    plan_source = st.session_state.get("plan_tasks") or st.session_state.get("plan", [])
    for rr, agent, t in route_tasks(plan_source, agents):
        role = rr
        task = f"{t['title']}: {t['description']}"
        logging.info(f"Executing agent {role} with task: {task}")
        with st.spinner(f"🤖 {role} working..."):
            try:
                memory_context = (
                    memory_manager.get_project_summaries(similar_ideas) if similar_ideas else ""
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
                result = call_openai(
                    model=sel["model"],
                    messages=[
                        {"role": "system", "content": agent.system_message},
                        {"role": "user", "content": prompt_with_context},
                    ],
                    **sel["params"],
                )["text"]
                result = (result or "").strip()
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
                for attempt in range(1, 3):  # attempt = 1 for first retry, 2 for second retry
                    # Prepare feedback context with failed criteria
                    feedback = ""
                    if failed_list:
                        feedback = f"The simulation indicates failure in: {', '.join(failed_list)}. Please address these issues in the design."
                    # Construct messages to re-run agent with feedback
                    try:
                        sel = pick_model(CallHints(stage="exec", difficulty="hard"))
                        logging.info(f"Model[exec]={sel['model']} params={sel['params']}")
                        new_result = call_openai(
                            model=sel["model"],
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
                        )["text"]
                        update_cost()
                        new_result = (new_result or "").strip()
                    except Exception as e:
                        new_result = result  # if the re-run fails, keep the last result
                    # Run simulation again on the revised output
                    new_metrics = simulation_agent.sim_manager.simulate(sim_type, new_result)
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
                        fail_desc = ", ".join(failed_list) if failed_list else "criteria"
                        result = (
                            new_result  # update result to the latest attempt for potential display
                        )
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
                safe_log_step(get_project_id(), role, "Output", "Passed Simulation", success=True)
                # Append simulation metrics to the output if no further refinement rounds
                if refinement_rounds == 1:
                    sim_text = simulation_agent.run_simulation(role, result)
                    if sim_text:
                        result = f"{result}\n\n{sim_text}"
        else:
            # Simulations not enabled or result is an error
            # Log the output as completed (success=True by default if no simulation)
            if not result.startswith("❌"):
                safe_log_step(get_project_id(), role, "Output", "Completed", success=True)
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
                        sim_rs = simulation_agent.run_simulation("Research Scientist", updated_rs)
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
                db.collection("rd_projects").document(doc_id).set(
                    {
                        "results": st.session_state["answers"],
                        "constraints": st.session_state.get("constraints", ""),
                        "risk_posture": st.session_state.get("risk_posture", "Medium"),
                    },
                    merge=True,
                )
            except Exception as e:
                logging.error(f"Save results failed: {e}")

    # Iterative refinement rounds if selected
    if refinement_rounds > 1:
        for r in range(2, refinement_rounds + 1):
            st.info(f"Refinement round {r-1} of {refinement_rounds-1}...")
            new_answers = {}
            plan_source = st.session_state.get("plan_tasks") or st.session_state.get("plan", [])
            for rr, agent, t in route_tasks(plan_source, agents):
                role = rr
                task = f"{t['title']}: {t['description']}"
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
                db.collection("rd_projects").document(doc_id).set(
                    {
                        "results": st.session_state["answers"],
                        "constraints": st.session_state.get("constraints", ""),
                        "risk_posture": st.session_state.get("risk_posture", "Medium"),
                    },
                    merge=True,
                )
            except Exception as e:
                logging.error(f"Save results failed: {e}")


def main():
    maybe_init_gcp_logging()
    project_id = get_project_id()
    db = None
    try:
        from google.cloud import firestore
        from google.oauth2 import service_account

        sa_info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(sa_info)
        gcp_project = sa_info.get("project_id")
        db = firestore.Client(credentials=credentials, project=gcp_project)
    except Exception as e:  # pragma: no cover - optional dependency
        logging.info(f"Firestore disabled: {e}")

    class _DummyWS:
        def log(self, msg: str) -> None:  # pragma: no cover - simple stub
            logging.debug(msg)

    ws = _DummyWS()
    use_firestore = False
    if db and project_id and st.session_state.get("project_saved"):
        try:
            ws = WS(project_id, st.session_state.get("project_name", ""))
            use_firestore = True
        except Exception:
            pass

    base_agents = get_agents()
    agents = dict(base_agents)

    memory_manager = get_memory_manager()
    st.session_state.setdefault("live_status", {})

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

    # Install a BudgetManager with the standard profile
    try:
        _mode_cfg, _budget = load_profile()
        models_cfg = dict(_mode_cfg.get("models", {}))
        resolved = {}
        for stage, name in models_cfg.items():
            resolved[stage] = select_model(stage, name)
        _mode_cfg["models"] = resolved
        st.session_state["MODE_CFG"] = _mode_cfg
        set_budget_manager(_budget)
    except Exception as _e:
        logging.info(f"Budget manager not installed: {str(_e)}")
    env_defaults = get_env_defaults()
    st.session_state["final_flags"] = env_defaults
    final_flags = env_defaults

    _mode_cfg["enable_images"] = bool(
        env_defaults.get("ENABLE_IMAGES", _mode_cfg.get("enable_images"))
    )
    _mode_cfg["web_search_calls_used"] = 0
    bootstrap = bootstrap_vector_index(_mode_cfg, logger)
    _mode_cfg["vector_index_present"] = bool(bootstrap.get("present"))
    _mode_cfg["vector_doc_count"] = int(bootstrap.get("doc_count", 0))
    _mode_cfg["vector_index_source"] = bootstrap.get("source", "none")
    _mode_cfg["vector_index_reason"] = bootstrap.get("reason", "")

    import config.feature_flags as ff
    from core.retrieval import budget as rbudget

    cap = rbudget.get_web_max_calls(os.environ, _mode_cfg)
    _mode_cfg["web_search_max_calls"] = cap
    _mode_cfg["live_search_max_calls"] = cap
    rbudget.RETRIEVAL_BUDGET = rbudget.RetrievalBudget(cap)
    ff.LIVE_SEARCH_MAX_CALLS = cap
    final_flags["LIVE_SEARCH_MAX_CALLS"] = cap
    snapshot_cfg = dict(_mode_cfg)
    snapshot_cfg.update(final_flags)
    snapshot_cfg["mode"] = "standard"
    budget_caps = {}
    if _mode_cfg.get("target_cost_usd") is not None:
        budget_caps["target_cost_usd"] = _mode_cfg.get("target_cost_usd")
    if budget_caps:
        snapshot_cfg["budget"] = budget_caps
    snapshot = build_resolved_config_snapshot(snapshot_cfg)
    logger.info("ResolvedConfig %s", json.dumps(snapshot, separators=(",", ":")))

    ff.VECTOR_INDEX_PRESENT = bool(_mode_cfg.get("vector_index_present"))
    ff.VECTOR_INDEX_PATH = _mode_cfg.get("vector_index_path") or ""
    ff.VECTOR_INDEX_SOURCE = _mode_cfg.get("vector_index_source") or "none"
    ff.VECTOR_INDEX_REASON = _mode_cfg.get("vector_index_reason") or ""
    ff.FAISS_BOOTSTRAP_MODE = _mode_cfg.get("faiss_bootstrap_mode", ff.FAISS_BOOTSTRAP_MODE)
    for k, v in final_flags.items():
        setattr(ff, k, v)

    ui_preset = UI_PRESETS["standard"]
    st.session_state["simulate_enabled"] = ui_preset["simulate_enabled"]
    st.session_state["design_depth"] = ui_preset["design_depth"]
    st.session_state["MODE"] = "standard"
    if hasattr(st, "caption"):
        st.caption(
            f"Profile: Standard • Depth={ui_preset['design_depth']} • "
            + f"Refinement rounds={ui_preset['refinement_rounds']} • "
            + f"Simulations={'on' if ui_preset['simulate_enabled'] else 'off'}"
        )

    # Orchestration -------------------------------------------------------------
    with _safe_expander(sidebar, "Orchestration", expanded=False):
        radio = getattr(st, "radio", lambda label, options, index=0, **k: options[index])
        number_input = getattr(st, "number_input", lambda label, value=0, **k: value)
        checkbox = getattr(st, "checkbox", lambda label, value=False, **k: value)
        default_engine = st.session_state.get("engine", "Classic")
        engines = ["Classic", "LangGraph", "AutoGen"]
        if not getattr(ff, "AUTOGEN_ENABLED", False):
            engines.remove("AutoGen")
        engine = radio("Engine", engines, index=engines.index(default_engine))
        st.session_state["engine"] = engine
        st.session_state["graph_enabled"] = engine == "LangGraph"
        max_conc = number_input("Max concurrency", min_value=1, value=int(st.session_state.get("max_concurrency", 1)), step=1)
        max_retries = number_input("Max retries", min_value=0, value=int(st.session_state.get("max_retries", 0)), step=1)
        backoff_base = number_input("Backoff base (s)", min_value=0.0, value=float(st.session_state.get("backoff_base", 1.0)), step=0.5)
        backoff_factor = number_input("Backoff factor", min_value=1.0, value=float(st.session_state.get("backoff_factor", 2.0)), step=0.5)
        backoff_max = number_input("Backoff max (s)", min_value=0.0, value=float(st.session_state.get("backoff_max", 30.0)), step=1.0)
        eval_toggle = checkbox("Enable evaluators", value=ff.EVALUATORS_ENABLED)
    st.session_state.update({
        "max_concurrency": int(max_conc),
        "max_retries": int(max_retries),
        "backoff_base": float(backoff_base),
        "backoff_factor": float(backoff_factor),
        "backoff_max": float(backoff_max),
        "evaluators_enabled": bool(eval_toggle),
    })
    ff.EVALUATORS_ENABLED = bool(eval_toggle)

    # Retrieval feature toggles -------------------------------------------------
    cfg = st.session_state["MODE_CFG"]
    with _safe_expander(sidebar, "Retrieval", expanded=False):
        checkbox = getattr(st, "checkbox", lambda label, value=False, **k: value)
        number_input = getattr(st, "number_input", lambda label, value=0, **k: value)
        selectbox = getattr(
            st,
            "selectbox",
            lambda label, options, index=0, **k: options[index],
        )
        rag_enabled = checkbox("Enable RAG (vector index)", value=cfg.get("rag_enabled", True))
        rag_top_k = number_input(
            "RAG top-K", min_value=1, value=int(cfg.get("rag_top_k", 5)), step=1
        )
        live_search_enabled = checkbox(
            "Enable Live Search", value=cfg.get("live_search_enabled", True)
        )
        live_search_backend = selectbox(
            "Live Search backend",
            ["openai", "serpapi"],
            index=0 if cfg.get("live_search_backend", "openai") == "openai" else 1,
        )
        live_search_max_calls = number_input(
            "Max live search calls",
            min_value=0,
            value=int(cfg.get("live_search_max_calls", 3)),
            step=1,
        )
        live_search_summary_tokens = number_input(
            "Live search summary tokens",
            min_value=0,
            value=int(cfg.get("live_search_summary_tokens", 256)),
            step=32,
        )

    overrides = {
        "rag_enabled": rag_enabled,
        "rag_top_k": int(rag_top_k),
        "live_search_enabled": live_search_enabled,
        "live_search_backend": live_search_backend,
        "live_search_max_calls": int(live_search_max_calls),
        "live_search_summary_tokens": int(live_search_summary_tokens),
    }

    with _safe_expander(sidebar, "Sources & KB", expanded=False):
        sources = st.session_state.get("session_sources", [])
        if sources:
            rows = [
                {
                    "title": s.get("title", ""),
                    "url": s.get("url", ""),
                    "date": s.get("when", ""),
                    "len": len(s.get("text", "")),
                }
                for s in sources
            ]
            getattr(st, "dataframe", lambda *a, **k: None)(rows)
        if st.button("Add selected to KB"):
            pass
        if st.button("Summarize & Store"):
            pass
        if st.button("Rebuild Vector Index"):
            pass
        auto = st.checkbox("Auto save cited sources to KB", value=False)
        st.session_state["auto_save_kb"] = auto
    with _safe_expander(sidebar, "Quality & Evaluation", expanded=False):
        checkbox = getattr(st, "checkbox", lambda label, value=False, **k: value)
        number_input = getattr(st, "number_input", lambda label, value=0, **k: value)
        evaluation_enabled = checkbox("Enable evaluation", value=cfg.get("evaluation_enabled", False))
        evaluation_max_rounds = number_input(
            "Evaluation max rounds",
            min_value=0,
            max_value=2,
            value=int(cfg.get("evaluation_max_rounds", 1)),
            step=1,
        )
        evaluation_human_review = checkbox(
            "Require human review",
            value=cfg.get("evaluation_human_review", True),
        )
    overrides.update(
        {
            "evaluation_enabled": evaluation_enabled,
            "evaluation_max_rounds": int(evaluation_max_rounds),
            "evaluation_human_review": evaluation_human_review,
        }
    )
    cfg.update(overrides)
    apply_overrides({k: v for k, v in overrides.items() if v is not None})
    rbudget.RETRIEVAL_BUDGET = rbudget.RetrievalBudget(cfg.get("live_search_max_calls", 0))

    # Budget controls -----------------------------------------------------------
    with _safe_expander(sidebar, "Budget", expanded=False):
        number_input = getattr(st, "number_input", lambda label, value=0.0, **k: value)
        target_budget = number_input(
            "Target budget (USD)",
            min_value=0.0,
            value=float(cfg.get("target_cost_usd", 0.0)),
            step=0.1,
        )
        cfg["target_cost_usd"] = float(target_budget)
        if BUDGET:
            BUDGET.target_cost_usd = float(target_budget)
        stage_weights_cfg = cfg.get("stage_weights", {})
        with _safe_expander(st, "Stage weights", expanded=False):
            plan_w = number_input(
                "Plan weight",
                min_value=0.0,
                value=float(stage_weights_cfg.get("plan", 0.0)),
                step=0.05,
            )
            exec_w = number_input(
                "Exec weight",
                min_value=0.0,
                value=float(stage_weights_cfg.get("exec", 0.0)),
                step=0.05,
            )
            synth_w = number_input(
                "Synth weight",
                min_value=0.0,
                value=float(stage_weights_cfg.get("synth", 0.0)),
                step=0.05,
            )
            total = plan_w + exec_w + synth_w
            if total > 0:
                stage_weights = {
                    "plan": plan_w / total,
                    "exec": exec_w / total,
                    "synth": synth_w / total,
                }
                cfg["stage_weights"] = stage_weights
                if BUDGET:
                    BUDGET.stage_weights = stage_weights

    # Tools configuration -------------------------------------------------------
    tool_cfg = st.session_state.get("TOOL_CFG", tool_router.TOOL_CONFIG.copy())
    with _safe_expander(sidebar, "Tools", expanded=False):
        checkbox = getattr(st, "checkbox", lambda label, value=False, **k: value)
        number_input = getattr(st, "number_input", lambda label, value=0, **k: value)
        code_enabled = checkbox(
            "Enable Code I/O", value=tool_cfg.get("CODE_IO", {}).get("enabled", True)
        )
        code_max_files = number_input(
            "Code I/O max_files",
            min_value=1,
            value=int(tool_cfg.get("CODE_IO", {}).get("max_files", 20)),
            step=1,
        )
        code_max_runtime = number_input(
            "Code I/O max_runtime_s",
            min_value=1,
            value=int(tool_cfg.get("CODE_IO", {}).get("max_runtime_s", 10)),
            step=1,
        )
        sim_enabled = checkbox(
            "Enable Simulation", value=tool_cfg.get("SIMULATION", {}).get("enabled", True)
        )
        sim_max_runtime = number_input(
            "Simulation max_runtime_s",
            min_value=1,
            value=int(tool_cfg.get("SIMULATION", {}).get("max_runtime_s", 30)),
            step=1,
        )
        vision_enabled = checkbox(
            "Enable Vision", value=tool_cfg.get("VISION", {}).get("enabled", True)
        )
        vision_max_runtime = number_input(
            "Vision max_runtime_s",
            min_value=1,
            value=int(tool_cfg.get("VISION", {}).get("max_runtime_s", 60)),
            step=1,
        )

    tool_cfg.setdefault("CODE_IO", {})
    tool_cfg.setdefault("SIMULATION", {})
    tool_cfg.setdefault("VISION", {})
    tool_cfg["CODE_IO"].update(
        {
            "enabled": bool(code_enabled),
            "max_files": int(code_max_files),
            "max_runtime_s": int(code_max_runtime),
        }
    )
    tool_cfg["SIMULATION"].update(
        {"enabled": bool(sim_enabled), "max_runtime_s": int(sim_max_runtime)}
    )
    tool_cfg["VISION"].update(
        {"enabled": bool(vision_enabled), "max_runtime_s": int(vision_max_runtime)}
    )
    st.session_state["TOOL_CFG"] = tool_cfg
    tool_router.TOOL_CONFIG.update(tool_cfg)

    # IP & Compliance ---------------------------------------------------------
    with _safe_expander(sidebar, "IP & Compliance", expanded=False):
        checkbox = getattr(st, "checkbox", lambda label, value=False, **k: value)
        text_input = getattr(st, "text_input", lambda label, value="", **k: value)
        multiselect = getattr(st, "multiselect", lambda label, options, default=None, **k: default or [])
        number_input = getattr(st, "number_input", lambda label, value=0.0, **k: value)
        patent_toggle = checkbox("Enable Patent APIs", value=ff.PATENT_APIS_ENABLED)
        regulatory_toggle = checkbox("Enable Regulatory APIs", value=ff.REGULATORY_APIS_ENABLED)
        compliance_toggle = checkbox("Enable Compliance Checks", value=ff.COMPLIANCE_ENABLED)
        ip_query = text_input("Query", value=st.session_state.get("ip_query", ""))
        ip_cpc = text_input("CPC", value=st.session_state.get("ip_cpc", ""))
        ip_assignee = text_input("Assignee", value=st.session_state.get("ip_assignee", ""))
        ip_date = text_input("Date range", value=st.session_state.get("ip_date", ""))
        profiles = multiselect(
            "Compliance profiles",
            ["us_federal", "eu_general", "california"],
            default=st.session_state.get("profiles", ["us_federal"]),
        )
        min_cov = number_input(
            "Min citation coverage",
            min_value=0.0,
            max_value=1.0,
            step=0.1,
            value=float(st.session_state.get("min_cov", 0.6)),
        )
    ff.PATENT_APIS_ENABLED = bool(patent_toggle)
    ff.REGULATORY_APIS_ENABLED = bool(regulatory_toggle)
    ff.COMPLIANCE_ENABLED = bool(compliance_toggle)
    st.session_state.update(
        {
            "ip_query": ip_query,
            "ip_cpc": ip_cpc,
            "ip_assignee": ip_assignee,
            "ip_date": ip_date,
            "profiles": profiles,
            "min_cov": float(min_cov),
        }
    )

    with st.expander("Patent Search", expanded=False):
        if st.button("Run Patent Search"):
            params = {
                k: v
                for k, v in {
                    "q": st.session_state.get("ip_query"),
                    "cpc": st.session_state.get("ip_cpc"),
                    "assignee": st.session_state.get("ip_assignee"),
                    "date_range": st.session_state.get("ip_date"),
                }.items()
                if v
            }
            st.session_state["patent_results"] = tool_router.call_tool(
                "UI", "patent_search", params
            )
        if st.session_state.get("patent_results"):
            getattr(st, "dataframe", lambda d, **k: None)(
                st.session_state["patent_results"]
            )

    with st.expander("Compliance Check", expanded=False):
        if st.button("Run Compliance Check") and st.session_state.get("final_doc"):
            from dr_rd.compliance import checker

            pids = st.session_state.get("profiles", ["us_federal"])
            profile = checker.load_profile(pids[0]) if pids else None
            if profile:
                rep = checker.check(
                    st.session_state.get("final_doc", ""), profile, {}
                )
                st.session_state["compliance_report"] = rep.model_dump()
        if st.session_state.get("compliance_report"):
            st.json(st.session_state["compliance_report"])

    project_names = []
    project_doc_ids = {}
    if db:
        try:
            docs = db.collection("rd_projects").stream()
            for doc in docs:
                data = doc.to_dict() or {}
                name = data.get("name") or doc.id
                project_doc_ids[name] = doc.id
            project_names = list(project_doc_ids.keys())
        except Exception as e:  # pragma: no cover - external service
            logging.error(f"Could not fetch projects from Firestore: {e}")
    else:
        project_names = [entry.get("name", "(unnamed)") for entry in memory_manager.data]

    current_project = st.session_state.get("project_name")
    if current_project and current_project not in project_names:
        project_names.append(current_project)

    selected_index = 0
    if "project_name" in st.session_state and st.session_state["project_name"] in project_names:
        selected_index = project_names.index(st.session_state["project_name"]) + 1
    selectbox_container = sidebar if hasattr(sidebar, "selectbox") else st
    selected_project = selectbox_container.selectbox(
        "🔄 Load Saved Project",
        ["(New Project)"] + project_names,
        index=selected_index,
    )

    last_selected = st.session_state.get("last_selected_project")
    if selected_project != last_selected:
        if selected_project != "(New Project)":
            if use_firestore:
                try:
                    doc_id = project_doc_ids.get(selected_project, selected_project)
                    doc = db.collection("rd_projects").document(doc_id).get()
                    if doc.exists:
                        data = doc.to_dict() or {}
                        st.session_state["idea"] = data.get("idea", "")
                        st.session_state["constraints"] = data.get("constraints", "")
                        st.session_state["risk_posture"] = data.get("risk_posture", "Medium")
                        plan_data = data.get("plan", [])
                        st.session_state["plan_tasks"] = plan_data
                        st.session_state["plan"] = [
                            {
                                "role": t.get("role", ""),
                                "title": t.get("title", ""),
                                "description": t.get("description", ""),
                            }
                            for t in plan_data
                        ]
                        st.session_state["answers"] = data.get("results", data.get("outputs", {}))
                        st.session_state["final_doc"] = data.get("proposal", "")
                        st.session_state["images"] = data.get("images", [])
                        st.session_state["project_name"] = data.get("name", selected_project)
                        st.session_state["project_saved"] = True
                        st.session_state["project_id"] = doc_id
                except Exception as e:  # pragma: no cover - external service
                    logging.error(f"Could not load project from Firestore: {e}")
            else:
                for entry in memory_manager.data:
                    if entry.get("name") == selected_project:
                        st.session_state["idea"] = entry.get("idea", "")
                        st.session_state["constraints"] = entry.get("constraints", "")
                        st.session_state["risk_posture"] = entry.get("risk_posture", "Medium")
                        plan_data = entry.get("plan", [])
                        st.session_state["plan_tasks"] = plan_data
                        st.session_state["plan"] = [
                            {
                                "role": t.get("role", ""),
                                "title": t.get("title", ""),
                                "description": t.get("description", ""),
                            }
                            for t in plan_data
                        ]
                        st.session_state["answers"] = entry.get("results", entry.get("outputs", {}))
                        st.session_state["final_doc"] = entry.get("proposal", "")
                        st.session_state["images"] = entry.get("images", [])
                        st.session_state["project_name"] = entry.get("name", selected_project)
                        st.session_state["project_saved"] = True
                        break
        else:
            for key in [
                "idea",
                "plan",
                "plan_tasks",
                "answers",
                "final_doc",
                "images",
                "project_name",
                "project_id",
                "project_saved",
                "constraints",
                "risk_posture",
            ]:
                st.session_state.pop(key, None)
        st.session_state["last_selected_project"] = selected_project
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()

    project_name = st.text_input("🏷️ Project Name:", value=st.session_state.get("project_name", ""))
    idea = st.text_input("🧠 Enter your project idea:", value=st.session_state.get("idea", ""))
    constraints = st.text_input(
        "Constraints (optional)",
        key="constraints",
        placeholder="Limits, compliance, vendors to avoid, deadlines…",
    )
    risk_posture = st.selectbox(
        "Risk posture",
        ["Low", "Medium", "High"],
        index=1,
        key="risk_posture",
    )

    if hasattr(st, "expander"):
        with st.expander("PoC", expanded=False):
            enable_poc = st.checkbox(
                "Enable PoC stage", value=st.session_state.get("enable_poc", False)
            )
            st.session_state["enable_poc"] = enable_poc
            sample = {
                "project_id": "demo-1",
                "hypothesis": "Cooling fin improves thermal performance by 15%.",
                "stop_on_fail": True,
                "tests": [
                    {
                        "id": "T1",
                        "title": "Thermal drop at 50W",
                        "inputs": {"power_w": 50, "ambient_c": 25, "_sim": "thermal_mock"},
                        "metrics": [
                            {"name": "delta_c", "operator": "<=", "target": 10.0, "unit": "C"},
                            {"name": "safety_margin", "operator": ">=", "target": 0.2},
                        ],
                        "safety_notes": "no external calls",
                    }
                ],
            }
            example = json.dumps(sample, indent=2)
            tp_text = st.text_area(
                "Test Plan (JSON)",
                value=st.session_state.get("test_plan_json", example),
                disabled=not enable_poc,
            )
            st.session_state["test_plan_json"] = tp_text
        if enable_poc:
            try:
                tp_obj = TestPlan.parse_raw(tp_text)
                st.session_state["test_plan"] = tp_obj
            except Exception as e:
                st.error(f"Invalid TestPlan: {e}")
                st.session_state.pop("test_plan", None)

    with _safe_expander(st, "Observability", expanded=False):
        st.session_state["save_decision_log"] = st.checkbox(
            "Save decision log",
            value=st.session_state.get("save_decision_log", False),
        )
        st.session_state["save_evidence_coverage"] = st.checkbox(
            "Save evidence & coverage",
            value=st.session_state.get("save_evidence_coverage", False),
        )
    with _safe_expander(st, "Build Spec", expanded=False):
        enable_build_spec = st.checkbox(
            "Generate Build Spec & Work Plan",
            value=st.session_state.get("enable_build_spec", False),
        )
        st.session_state["enable_build_spec"] = enable_build_spec
        os.environ["DRRD_ENABLE_BUILD_SPEC"] = "true" if enable_build_spec else "false"
    idea_input = idea
    submitted_idea_text = idea
    if not idea:
        st.info("Please describe an idea to get started.")
        st.stop()
    slug_candidate = _slugify(project_name)
    duplicate = bool(
        project_name
        and db
        and slug_candidate in project_doc_ids.values()
        and not st.session_state.get("project_saved")
    )
    st.session_state["project_name"] = project_name

    similar_ideas = memory_manager.find_similar_ideas(idea)
    if similar_ideas:
        st.info("Found similar past projects: " + ", ".join(similar_ideas))

    disable_btn = not project_name or duplicate
    try:
        clicked = st.button("1⃣ Generate Research Plan", disabled=disable_btn)
    except TypeError:  # older streamlit versions
        clicked = st.button("1⃣ Generate Research Plan")
        if disable_btn:
            if not project_name:
                st.info("Please provide a project name to get started.")
            elif duplicate:
                st.warning("Project name already exists. Please choose a unique name.")
            st.stop()
    if disable_btn and not clicked:
        if not project_name:
            st.info("Please provide a project name to get started.")
        elif duplicate:
            st.warning("Project name already exists. Please choose a unique name.")
        st.stop()

    if clicked:
        logging.info(f"User generated plan for idea: {idea}")
        if db and not st.session_state.get("project_saved"):
            try:
                WS(slug_candidate, project_name)
                st.session_state["project_saved"] = True
            except Exception as e:
                logging.error(f"Init project failed: {e}")
        try:
            with st.spinner("📝 Planning..."):
                agent = PlannerAgent()
                tasks = agent.run(idea, "")
                update_cost()
            if isinstance(tasks, dict):
                tasks = tasks.get("tasks", [])
            st.session_state["plan"] = tasks
            st.session_state["plan_tasks"] = tasks
            allowed_roles = set(get_agents().keys())
            normalized = normalize_roles_tasks(tasks, allowed_roles=allowed_roles, max_roles=None)
            st.session_state["plan_normalized_tasks"] = normalized
            st.session_state["allowed_roles"] = allowed_roles
            logger.info("Planner tasks: %d", len(tasks))
            logger.info(
                "Planner tasks total=%d canonical_roles=%d",
                len(tasks),
                len({t["normalized_role"] for t in normalized}),
            )
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
                    db.collection("rd_projects").document(doc_id).set(
                        {
                            "name": st.session_state.get("project_name", ""),
                            "idea": submitted_idea_text or idea_input or "",
                            "constraints": st.session_state.get("constraints", ""),
                            "risk_posture": st.session_state.get("risk_posture", "Medium"),
                            "plan": tasks,
                        },
                        merge=True,
                    )
                except Exception as e:
                    logging.error(f"Save plan failed: {e}")
            render_cost_summary(st.session_state.get("plan"))
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
        raw_tasks = st.session_state["plan"]
        raw_tasks = raw_tasks.get("tasks", []) if isinstance(raw_tasks, dict) else raw_tasks
        if not raw_tasks:
            getattr(st, "error", lambda *a, **k: None)(
                "Planner returned no valid tasks. Check logs."
            )
        else:
            allowed_roles = st.session_state.get("allowed_roles", set())
            radio_fn = getattr(st, "radio", lambda *a, **k: "Canonical (unified)")
            view = radio_fn(
                "Role view",
                ["Canonical (unified)", "Original (all roles)"],
                index=0,
                horizontal=True,
            )
            max_roles = None
            if view.startswith("Canonical"):
                max_roles = st.slider(
                    "Max canonical roles",
                    3,
                    len(allowed_roles),
                    min(9, len(allowed_roles)),
                )
                normalized_tasks = normalize_roles_tasks(
                    raw_tasks,
                    allowed_roles=allowed_roles,
                    max_roles=max_roles,
                )
                grouped = group_by_role(normalized_tasks, key="normalized_role")
            else:
                grouped = group_by_role(
                    [{**t, "normalized_role": t.get("role", "")} for t in raw_tasks],
                    key="normalized_role",
                )

            for role, items in grouped.items():
                st.subheader(role)
                for t in items:
                    title = t.get("title", "")
                    if view.startswith("Canonical") and t.get("role") != t.get("normalized_role"):
                        title = f"[{t['role']}] {title}"
                    st.markdown(f"- **{title}**")
                    st.caption(t.get("description", ""))

            logger.info(
                f"Planner view={view} max_roles={max_roles if view.startswith('Canonical') else 'NA'}"
            )

        refinement_rounds = ui_preset["refinement_rounds"]
        simulate_enabled = st.session_state.get("simulate_enabled", True)
        design_depth = st.session_state.get("design_depth", "Low")
        re_run_simulations = ui_preset["rerun_sims_each_round"]

        if st.button("2⃣ Run All Domain Experts"):
            with st.spinner("🤖 Running domain experts..."):
                try:
                    tasks = st.session_state.get("plan", [])
                    ui_model = st.session_state.get("model")
                    engine = st.session_state.get("engine", "Classic")
                    if engine == "LangGraph":
                        if run_langgraph is None:
                            st.error("LangGraph not installed")
                            raise RuntimeError("LangGraph unavailable")
                        constraints = st.session_state.get("constraints", [])
                        if isinstance(constraints, str):
                            constraints = [c.strip() for c in constraints.splitlines() if c.strip()]
                        final, answers, trace_bundle = run_langgraph(
                            idea,
                            constraints,
                            st.session_state.get("risk_posture", "medium"),
                            ui_model=ui_model,
                            max_concurrency=st.session_state.get("max_concurrency", 1),
                            max_retries=st.session_state.get("max_retries", 0),
                            retry_backoff={
                                "base_s": st.session_state.get("backoff_base", 1.0),
                                "factor": st.session_state.get("backoff_factor", 2.0),
                                "max_s": st.session_state.get("backoff_max", 30.0),
                            },
                            evaluators_enabled=st.session_state.get("evaluators_enabled", False),
                        )
                        st.session_state["answers"] = answers
                        st.session_state["final_doc"] = final
                        st.session_state["graph_trace_bundle"] = trace_bundle
                        st.session_state["session_sources"] = trace_bundle.get("retrieval_trace", [])
                        slug = get_project_id() or "default"
                        outdir = Path("audits") / slug
                        outdir.mkdir(parents=True, exist_ok=True)
                        (outdir / "graph_trace.json").write_text(
                            json.dumps(trace_bundle, indent=2), encoding="utf-8"
                        )
                        render_cost_summary(tasks)
                    elif engine == "AutoGen":
                        if run_autogen is None:
                            st.error("AutoGen not installed")
                            raise RuntimeError("AutoGen unavailable")
                        final, answers, trace_bundle = run_autogen(idea)
                        st.session_state["answers"] = answers
                        st.session_state["final_doc"] = final
                        st.session_state["graph_trace_bundle"] = trace_bundle
                        st.session_state["session_sources"] = trace_bundle.get("retrieval_trace", [])
                        slug = get_project_id() or "default"
                        outdir = Path("audits") / slug
                        outdir.mkdir(parents=True, exist_ok=True)
                        (outdir / "autogen_trace.json").write_text(
                            json.dumps(trace_bundle, indent=2), encoding="utf-8"
                        )
                        render_cost_summary(tasks)
                    else:
                        results = execute_plan(
                            idea,
                            tasks,
                            project_id=get_project_id(),
                            save_decision_log=st.session_state.get(
                                "save_decision_log", False
                            ),
                            save_evidence=st.session_state.get(
                                "save_evidence_coverage", False
                            ),
                            project_name=st.session_state.get("project_name"),
                            ui_model=ui_model,
                        )
                        st.session_state["answers"] = results
                        render_cost_summary(st.session_state.get("plan"))
                    if (
                        engine == "Classic"
                        and st.session_state.get("awaiting_approval")
                    ):
                        pending = st.session_state.get("pending_followups", [])
                        st.info("Evaluation suggests follow-ups:")
                        for fu in pending:
                            st.markdown(f"- **{fu.get('role','')}**: {fu.get('title','')}")
                        if st.button("Approve follow-ups", key="approve_followups"):
                            tasks2 = st.session_state.pop("pending_followups", [])
                            st.session_state["awaiting_approval"] = False
                            more = execute_plan(
                                idea,
                                tasks2,
                                project_id=get_project_id(),
                                save_decision_log=st.session_state.get("save_decision_log", False),
                                save_evidence=st.session_state.get("save_evidence_coverage", False),
                                project_name=st.session_state.get("project_name"),
                                ui_model=ui_model,
                            )
                            st.session_state["answers"].update(more)
                        if st.button("Reject follow-ups", key="reject_followups"):
                            st.session_state["awaiting_approval"] = False
                            st.session_state.pop("pending_followups", None)
                except openai.OpenAIError as e:
                    logging.exception("OpenAI error during plan execution: %s", e)
                    getattr(st, "error", lambda *a, **k: None)(
                        "Execution failed: Unable to run domain experts. Please check your API key or try again later."
                    )
                except Exception as e:  # pylint: disable=broad-except
                    logging.exception("Unexpected error during plan execution: %s", e)
                    getattr(st, "error", lambda *a, **k: None)(
                        "Execution failed: An unexpected error occurred."
                    )
                else:
                    getattr(st, "success", lambda *a, **k: None)("✅ Domain experts complete!")

    render_live_status(st.session_state.get("live_status", {}))
    agent_trace = st.session_state.get("agent_trace")
    if agent_trace:
        render_agent_trace(agent_trace, st.session_state.get("answers", {}))
        render_exports(get_project_id() or "", agent_trace)
    render_role_summaries(st.session_state.get("answers", {}))
    if st.button("3⃣ Compile Final Proposal"):
        logging.info("User compiled final proposal")
        with st.spinner("🚀 Synthesizing final R&D proposal..."):
            try:
                if st.session_state.get("graph_enabled") and st.session_state.get(
                    "final_doc"
                ):
                    final_report_text = st.session_state["final_doc"]
                    images: List[str] = []
                else:
                    result = compose_final_proposal(
                        idea,
                        st.session_state["answers"],
                    )
                    final_report_text = result.get("document", "")
                    images = result.get("images", [])
                update_cost()
                memory_manager.store_project(
                    st.session_state.get("project_name", ""),
                    idea,
                    st.session_state.get(
                        "plan_tasks", st.session_state.get("plan", {})
                    ),
                    st.session_state["answers"],
                    final_report_text,
                    images,
                    constraints=st.session_state.get("constraints", ""),
                    risk_posture=st.session_state.get("risk_posture", "Medium"),
                )
                st.session_state["final_doc"] = final_report_text
            except Exception as e:  # pylint: disable=broad-except
                getattr(st, "error", lambda *a, **k: None)(
                    f"Final proposal synthesis failed: {e}"
                )
                logging.exception("Error during final proposal synthesis: %s", e)
                st.stop()
            st.session_state["final_doc"] = final_report_text
            if two_pass_enabled():
                try:
                    summaries: List[RoleSummary] = []
                    for role, content in st.session_state.get("answers", {}).items():
                        bullets = [
                            line.strip("- ").strip()
                            for line in content.splitlines()
                            if line.strip()
                        ][:5]
                        summaries.append(RoleSummary(role=role, bullets=bullets))
                    st.session_state["integrated_summary"] = integrate(summaries)
                except Exception as e:
                    logging.warning("Summary integration failed: %s", e)
            if use_firestore:
                try:
                    doc_id = get_project_id()
                    db.collection("rd_projects").document(doc_id).set(
                        {
                            "proposal": final_report_text,
                            "constraints": st.session_state.get("constraints", ""),
                            "risk_posture": st.session_state.get("risk_posture", "Medium"),
                            "trace_ref": f"audits/{doc_id}/trace.json",
                        },
                        merge=True,
                    )
                except Exception as e:
                    logging.error(f"Save proposal failed: {e}")

    if "final_doc" in st.session_state:
        st.subheader("📖 Integrated R&D Proposal")
        doc_text = st.session_state["final_doc"]
        st.markdown(doc_text)
        pdf_bytes = generate_pdf(doc_text)
        if hasattr(st, "download_button"):
            st.download_button(
                label="📄 Download Final Report as PDF",
                data=pdf_bytes,
                file_name="R&D_Report.pdf",
                mime="application/pdf",
            )
        summary = st.session_state.get("integrated_summary")
        if summary and summary.contradictions:
            exp_fn = getattr(st, "expander", None)
            container = (
                exp_fn("⚠️ Cross-role contradictions & resolutions", expanded=False)
                if callable(exp_fn)
                else st
            )
            with container:
                for item in summary.contradictions:
                    st.markdown(f"- {item}")

        slug = get_project_id()
        build_dir = os.path.join("audits", slug, "build") if slug else None
        if build_dir and os.path.exists(build_dir):
            st.subheader("📦 Build Spec")
            files = [
                "SDD.md",
                "ImplementationPlan.md",
                "bom.csv",
                "budget.csv",
            ]
            for fname in files:
                path = os.path.join(build_dir, fname)
                if os.path.exists(path) and hasattr(st, "download_button"):
                    mode = "rb" if fname.endswith(".csv") else "r"
                    with open(path, mode) as f:
                        data = f.read()
                    st.download_button(
                        f"Download {fname}",
                        data,
                        file_name=fname,
                        mime="text/csv" if fname.endswith(".csv") else "text/markdown",
                    )

        report = st.session_state.get("poc_report")
        if report:
            st.subheader("🔬 PoC Results")
            rows = [{"test_id": r.test_id, "passed": r.passed} for r in report.results]
            st.table(pd.DataFrame(rows))
            if hasattr(st, "download_button"):
                st.download_button(
                    "Download poc_report.json",
                    json.dumps(report.dict(), indent=2),
                    file_name="poc_report.json",
                    mime="application/json",
                )
                import csv as _csv
                import io

                buf = io.StringIO()
                writer = _csv.writer(buf)
                writer.writerow(
                    ["test_id", "passed", "metrics_observed", "metrics_passfail", "notes"]
                )
                for r in report.results:
                    writer.writerow(
                        [r.test_id, r.passed, r.metrics_observed, r.metrics_passfail, r.notes]
                    )
                st.download_button(
                    "Download poc_results.csv",
                    buf.getvalue(),
                    file_name="poc_results.csv",
                    mime="text/csv",
                )

        # --- App Builder (inline) ---
        if build_app_from_idea:
            st.subheader("🔧 Generate a Streamlit App from this idea")
            st.caption(
                "This will plan a small Streamlit project and write files under `generated_apps/<slug>/`."
            )
            try:
                gen = st.button("Generate Streamlit app", type="primary")
            except TypeError:  # fallback for older Streamlit versions
                gen = st.button("Generate Streamlit app")
            if gen:
                import io
                import zipfile

                with st.spinner("Planning and generating app files..."):
                    spec, files = build_app_from_idea(idea)
                st.success(f"App scaffold created → generated_apps/{spec.slug}")
                with st.expander("Preview generated files", expanded=False):
                    for p in sorted(files):
                        st.write(f"**{p}**")
                        if p.endswith(".py") or p.endswith(".md") or p.endswith(".txt"):
                            st.code(
                                files[p][:1000], language="python" if p.endswith(".py") else None
                            )
                        else:
                            st.text(f"(binary or long content; {len(files[p])} bytes)")

                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
                    for path, content in files.items():
                        z.writestr(path, content)
                buf.seek(0)
                st.download_button(
                    "Download app as ZIP", data=buf.read(), file_name=f"{spec.slug}.zip"
                )

                # --- QA & Publish controls ---
                if qa_all and "spec" in locals():
                    st.subheader("✅ Optional: QA checks")
                    if st.button("Run QA checks"):
                        app_root = f"generated_apps/{spec.slug}"
                        report = qa_all(app_root)
                        st.write("**Requirements (patched):**", report["requirements"])
                        if report["syntax_errors"]:
                            st.error("Syntax issues found:")
                            for f, msg in report["syntax_errors"].items():
                                st.write(f"- {f}: {msg}")
                        st.code(report["pytest_output"][:2000])
                        if report["pytest_exit"] == 0:
                            st.success("Pytest passed")
                        else:
                            st.warning(f"Pytest exit code: {report['pytest_exit']}")

                if make_zip_bytes and "spec" in locals():
                    st.subheader("🚀 Optional: Publish")
                    repo_name = st.text_input("New GitHub repo name", value=spec.slug)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Download repo ZIP"):
                            app_root = f"generated_apps/{spec.slug}"
                            write_publishing_md(app_root, repo_name)
                            z = make_zip_bytes(app_root)
                            st.download_button(
                                f"Download {repo_name}.zip", data=z, file_name=f"{repo_name}.zip"
                            )
                    with col2:
                        if st.button("Create GitHub repo via API (uses GH_PAT)"):
                            token = st.secrets.get("GH_PAT", "")
                            if not token:
                                st.error("GH_PAT secret not found. Add it in Streamlit secrets.")
                            else:
                                ok, info = try_create_github_repo(
                                    repo_name,
                                    f"Generated by DR-RD App Builder: {spec.name}",
                                    token,
                                    private=False,
                                )
                                if ok:
                                    st.success(f"Repo created: {info.get('html_url')}")
                                else:
                                    st.warning(f"Could not create repo: {info}")
        # --- end App Builder ---

        by_stage = METER.by_stage()
        df = pd.DataFrame(
            [
                {"stage": k, "tokens": v, "dollars_est": v / 1000 * 0.005}
                for k, v in by_stage.items()
            ]
        )
        if not df.empty:
            df = df.sort_values("tokens", ascending=False)
            getattr(st, "caption", lambda *a, **k: None)("Token breakdown by stage")
            getattr(st, "dataframe", lambda *a, **k: None)(df, use_container_width=True)

    # Tool panels ---------------------------------------------------------------
    tool_cfg = st.session_state.get("TOOL_CFG", tool_router.TOOL_CONFIG)
    st.subheader("🛠 Tools")
    tab_code, tab_sim, tab_vis, tab_exp = getattr(st, "tabs", lambda labels: [st] * len(labels))(
        ["Code I/O", "Simulation", "Vision", "Exports"]
    )
    with tab_code:
        globs = st.text_input("Globs (comma-sep)")
        if st.button("Read Repo", disabled=not tool_cfg.get("CODE_IO", {}).get("enabled", True)):
            try:
                patterns = [g.strip() for g in globs.split(",") if g.strip()]
                res = tool_router.call_tool("UI", "read_repo", {"globs": patterns})
                files = res.get("results", []) if isinstance(res, dict) else res
                for item in files:
                    st.write(f"**{item.get('path','')}**")
                    st.code(item.get("text", ""), language="markdown")
                if res.get("truncated"):
                    st.info("Results truncated")
            except Exception as e:
                st.error(str(e))
        diff = st.text_area("Unified diff (preview)")
        if st.button(
            "Preview Patch", disabled=not tool_cfg.get("CODE_IO", {}).get("enabled", True)
        ):
            try:
                plan = tool_router.call_tool("UI", "plan_patch", {"diff_spec": diff})
                st.code(plan)
            except Exception as e:
                st.error(str(e))
        if st.button(
            "Apply Patch", disabled=not tool_cfg.get("CODE_IO", {}).get("enabled", True)
        ):
            st.session_state["pending_patch"] = diff
        if st.session_state.get("pending_patch"):
            st.warning("Apply patch? This cannot be undone.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Confirm Apply"):
                    try:
                        tool_router.call_tool(
                            "UI",
                            "apply_patch",
                            {"diff": st.session_state.pop("pending_patch"), "dry_run": False},
                        )
                        st.success("Patch applied")
                    except Exception as e:
                        st.error(str(e))
            with col2:
                if st.button("Cancel"):
                    st.session_state.pop("pending_patch", None)
    with tab_sim:
        params_text = st.text_area("Params (JSON)", value="{}")
        run_single = st.button(
            "Run Simulation", disabled=not tool_cfg.get("SIMULATION", {}).get("enabled", True)
        )
        run_sweep = st.button(
            "Run Sweep", disabled=not tool_cfg.get("SIMULATION", {}).get("enabled", True)
        )
        run_mc = st.button(
            "Run Monte Carlo", disabled=not tool_cfg.get("SIMULATION", {}).get("enabled", True)
        )
        if run_single or run_sweep or run_mc:
            try:
                params = json.loads(params_text or "{}")
                if run_sweep:
                    params = {"sweep": params if isinstance(params, list) else [params]}
                elif run_mc:
                    params.setdefault("monte_carlo", 10)
                result = tool_router.call_tool("UI", "simulate", params)
                st.json(result)
            except Exception as e:
                st.error(str(e))
    with tab_vis:
        tasks = st.multiselect("Tasks", ["ocr", "classify", "detect"])
        image_file = st.file_uploader("Image", type=["png", "jpg", "jpeg"])
        video_file = st.file_uploader("Video", type=["mp4", "mov", "avi"])
        sample_rate = st.number_input("sample_rate_fps", min_value=1, value=1)
        if st.button(
            "Analyze Image", disabled=not tool_cfg.get("VISION", {}).get("enabled", True)
        ) and image_file:
            try:
                result = tool_router.call_tool(
                    "UI", "analyze_image", {"file_or_bytes": image_file.getvalue(), "tasks": tasks}
                )
                st.json(result)
            except Exception as e:
                st.error(str(e))
        if st.button(
            "Analyze Video", disabled=not tool_cfg.get("VISION", {}).get("enabled", True)
        ) and video_file:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(video_file.name).suffix) as tmp:
                    tmp.write(video_file.getvalue())
                    tmp_path = tmp.name
                try:
                    result = tool_router.call_tool(
                        "UI",
                        "analyze_video",
                        {
                            "file_path": tmp_path,
                            "sample_rate_fps": int(sample_rate),
                            "tasks": tasks,
                        },
                    )
                    st.json(result)
                finally:
                    os.unlink(tmp_path)
            except Exception as e:
                st.error(str(e))
    with tab_exp:
        if st.button("Download Tool-Call Trace (JSON)"):
            trace = tool_router.get_provenance()
            slug = get_project_id() or "default"
            outdir = Path("audits") / slug
            outdir.mkdir(parents=True, exist_ok=True)
            fp = outdir / "tool_trace.json"
            fp.write_text(json.dumps(trace, indent=2), encoding="utf-8")
            st.download_button(
                "tool_trace.json", json.dumps(trace, indent=2), file_name="tool_trace.json"
            )
        if st.session_state.get("graph_enabled") and st.session_state.get("graph_trace_bundle"):
            st.download_button(
                "Download Graph Trace (JSON)",
                json.dumps(st.session_state["graph_trace_bundle"], indent=2),
                file_name="graph_trace.json",
            )
        if st.button("Download Sources (JSONL)"):
            from core.retrieval import provenance

            sources = provenance.get_trace()
            payload = "\n".join(json.dumps(s) for s in sources)
            slug = get_project_id() or "default"
            outdir = Path("audits") / slug
            outdir.mkdir(parents=True, exist_ok=True)
            fp = outdir / "sources.jsonl"
            fp.write_text(payload, encoding="utf-8")
            st.download_button("sources.jsonl", payload, file_name="sources.jsonl")
        if st.button("Download Final Report (Markdown)") and st.session_state.get("final_doc"):
            slug = get_project_id() or "default"
            outdir = Path("audits") / slug
            outdir.mkdir(parents=True, exist_ok=True)
            fp = outdir / "final_report.md"
            fp.write_text(st.session_state["final_doc"], encoding="utf-8")
            st.download_button(
                "final_report.md",
                st.session_state["final_doc"],
                file_name="final_report.md",
            )

    st.subheader("💬 Project Chat")
    doc_id = get_project_id()
    prior_chat = []
    if use_firestore:
        try:
            snap = db.collection("rd_projects").document(doc_id).get()
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
            context_bits.append(f"PLAN ROLES: {', '.join(st.session_state['plan'].keys())}")
        if st.session_state.get("answers"):
            sums = [
                f"{r}: {len((st.session_state['answers'].get(r) or ''))} chars"
                for r in st.session_state["answers"].keys()
            ]
            context_bits.append("OUTPUTS: " + "; ".join(sums))
        if st.session_state.get("final_doc"):
            context_bits.append("PROPOSAL: present")

        from core.model_router import CallHints, pick_model

        sel = pick_model(CallHints(stage="exec", deep_reasoning=False))
        msg = "\n\n".join(context_bits) + f"\n\nUser: {user_msg}"
        try:
            reply = call_openai(
                model=sel["model"],
                messages=[
                    {
                        "role": "system",
                        "content": "You are the project's on-call R&D assistant.",
                    },
                    {"role": "user", "content": msg},
                ],
                **sel["params"],
            )["text"]
            reply = (reply or "").strip()
        except Exception as e:
            reply = f"(assistant error: {e})"
        new_chat = prior_chat + [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": reply},
        ]
        if use_firestore:
            try:
                db.collection("rd_projects").document(doc_id).set(
                    {
                        "chat": new_chat,
                        "constraints": st.session_state.get("constraints", ""),
                        "risk_posture": st.session_state.get("risk_posture", "Medium"),
                    },
                    merge=True,
                )
            except Exception as e:
                logging.error(f"Save chat failed: {e}")
        getattr(st, "markdown", print)(f"**Assistant:** {reply}")


# Validate and log agent registry once at startup
_summary = validate_registry(strict=False)
logger.info(
    "Agent registry validation: ok=%d, errors=%d",
    len(_summary["ok"]),
    len(_summary["errors"]),
)
if _summary["errors"]:
    logger.info("Non-callable agents: %s", [n for n, _ in _summary["errors"]])
