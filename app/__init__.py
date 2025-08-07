from app.logging_setup import init_gcp_logging
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
import re
import uuid
import io
import fitz
from markdown_pdf import MarkdownPdf, Section

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


def get_project_id() -> str:
    """Return a project id from session state, creating one if needed."""
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
                response = openai.chat.completions.create(
                    model=agent.model,
                    messages=[
                        {"role": "system", "content": agent.system_message},
                        {"role": "user", "content": prompt_with_context},
                    ],
                )
                result = response.choices[0].message.content.strip()
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
                        revised_response = openai.chat.completions.create(
                            model=agent.model,
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
                        )
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
                            st.error(
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


def main():
    maybe_init_gcp_logging()

    agents = get_agents()
    memory_manager = get_memory_manager()

    use_firestore = False
    try:
        from google.cloud import firestore

        db = firestore.Client()
        use_firestore = True
    except Exception as e:  # pragma: no cover - optional dependency
        logging.info(f"Firestore not enabled, using local storage: {e}")

    get_project_id()

    st.set_page_config(page_title="Dr. R&D", layout="wide")
    st.title("Dr. R&D")

    sidebar = getattr(st, "sidebar", st)
    if hasattr(sidebar, "title"):
        sidebar.title("Configuration")
    else:
        st.markdown("## Configuration")

    project_names = []
    project_doc_ids = {}
    if use_firestore:
        try:
            docs = db.collection("projects").stream()
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
        if selected_project != "(New Project)":
            if use_firestore:
                try:
                    doc_id = project_doc_ids.get(selected_project, selected_project)
                    doc = db.collection("projects").document(doc_id).get()
                    if doc.exists:
                        data = doc.to_dict() or {}
                        st.session_state["idea"] = data.get("idea", "")
                        st.session_state["plan"] = data.get("plan", {})
                        st.session_state["answers"] = data.get("outputs", {})
                        st.session_state["final_doc"] = data.get("proposal", "")
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
                "project_name",
                "project_id",
            ]:
                st.session_state.pop(key, None)
        st.session_state["last_selected_project"] = selected_project
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()

    if "simulate_enabled" not in st.session_state:
        st.session_state["simulate_enabled"] = True
    if "design_depth" not in st.session_state:
        st.session_state["design_depth"] = "Low"
    if "auto_mode" not in st.session_state:
        st.session_state["auto_mode"] = False

    form_container = sidebar if hasattr(sidebar, "form") else st
    with form_container.form("config_form"):
        simulate_enabled = st.checkbox(
            "Enable Simulations", value=st.session_state["simulate_enabled"]
        )
        design_depth = st.selectbox(
            "Design Depth",
            options=["Low", "Medium", "High"],
            index=["Low", "Medium", "High"].index(st.session_state["design_depth"]),
            help="Controls how detailed the agent outputs will be.",
        )
        auto_mode = st.checkbox(
            "Enable Automatic AI R&D (HRM)", value=st.session_state["auto_mode"]
        )
        submitted = st.form_submit_button("Apply settings")
    if submitted:
        st.session_state["simulate_enabled"] = simulate_enabled
        st.session_state["design_depth"] = design_depth
        st.session_state["auto_mode"] = auto_mode

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

    if st.button("1⃣ Generate Research Plan"):
        logging.info(f"User generated plan for idea: {idea}")
        try:
            with st.spinner("📝 Planning..."):
                raw_plan = agents["Planner"].run(
                    idea, "Break down the project into role-specific tasks"
                )
                if not isinstance(raw_plan, dict):
                    st.error(
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
        except openai.OpenAIError as e:
            logging.exception("OpenAI error during plan generation: %s", e)
            st.error(
                "Planning failed: Unable to generate plan. Please check your API key or try again later."
            )
            st.write("Plan generation failed:", e)
        except Exception as e:  # pylint: disable=broad-except
            logging.exception("Unexpected error during plan generation: %s", e)
            st.error("Planning failed: An unexpected error occurred.")
            st.write("Plan generation failed:", e)

    if "plan" in st.session_state:
        st.subheader("Project Plan (Role → Task)")
        st.json(st.session_state["plan"])

        refinement_rounds = st.slider("🔁 Refinement Rounds", 1, 3, value=1)
        simulate_enabled = st.session_state.get("simulate_enabled", True)
        design_depth = st.session_state.get("design_depth", "Low")
        re_run_simulations = (
            st.checkbox("Re-run simulations after each refinement round", value=False)
            if simulate_enabled
            else False
        )

        def run_pipeline(project_id: str, idea: str) -> None:
            run_manual_pipeline(
                agents,
                memory_manager,
                similar_ideas,
                idea,
                refinement_rounds,
                simulate_enabled,
                design_depth,
                re_run_simulations,
            )

        if st.button("2⃣ Run All Domain Experts"):
            project_id = get_project_id()
            if st.session_state.get("auto_mode", False):
                from dr_rd.hrm_engine import HRMLoop

                with st.spinner("🤖 Running hierarchical plan → execute → revise…"):
                    state, report = HRMLoop(project_id, idea).run()
                st.success("✅ HRM Automatic R&D complete!")
                if report:
                    st.subheader("Final Report")
                    st.markdown(report)
                    pdf = generate_pdf(report)
                    st.download_button(
                        "📄 Download Report",
                        data=pdf,
                        file_name="R&D_Report.pdf",
                        mime="application/pdf",
                    )
                st.subheader("Results")
                st.json(state.get("results", {}))
            else:
                run_pipeline(project_id, idea)

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
                        planner_resp = openai.chat.completions.create(
                            model=planner_agent.model,
                            messages=[
                                {
                                    "role": "system",
                                    "content": planner_agent.system_message,
                                },
                                {"role": "user", "content": planner_query},
                            ],
                        )
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
                        revised_resp = openai.chat.completions.create(
                            model=domain_agent.model,
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
                        )
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
                                st.success(
                                    f"Accepted revision for {role}. The output has been updated."
                                )
                            if continue_discussion:
                                st.info(
                                    f"You can refine your suggestion for {role} and submit again."
                                )
                    except Exception as e:  # pylint: disable=broad-except
                        st.error(f"Failed to process suggestion for {role}: {e}")

        if st.button("3⃣ Compile Final Proposal"):
            logging.info("User compiled final proposal")
            with st.spinner("🚀 Synthesizing final R&D proposal..."):
                try:
                    final_doc = compose_final_proposal(
                        idea,
                        st.session_state["answers"],
                        include_simulations=st.session_state.get(
                            "simulate_enabled", True
                        ),
                    )
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
                    )
                except Exception as e:  # pylint: disable=broad-except
                    st.error(f"Final proposal synthesis failed: {e}")
                    logging.exception("Error during final proposal synthesis: %s", e)
                    st.stop()
            st.session_state["final_doc"] = final_doc

    if "final_doc" in st.session_state:
        st.subheader("📖 Integrated R&D Proposal")
        st.markdown(st.session_state["final_doc"])
        pdf_bytes = generate_pdf(st.session_state["final_doc"])
        if hasattr(st, "download_button"):
            st.download_button(
                label="📄 Download Final Report as PDF",
                data=pdf_bytes,
                file_name="R&D_Report.pdf",
                mime="application/pdf",
            )
