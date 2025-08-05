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
import uuid
import io
import fitz
from markdown_pdf import MarkdownPdf, Section


def generate_pdf(markdown_text):
    pdf = MarkdownPdf(toc_level=2)
    pdf.add_section(Section(markdown_text))
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


def main():
    maybe_init_gcp_logging()

    # --- Instantiate Agents ---
    agents = initialize_agents()

    # Initialize persistent memory manager
    memory_manager = MemoryManager()
    # Set or generate a project_id for logging
    if "project_id" not in st.session_state:
        st.session_state["project_id"] = str(uuid.uuid4())

    st.set_page_config(page_title="DR-RD Phase 6: Simulated Multi-Agent R&D", layout="wide")
    st.title("DR-RD AI R&D Engine — Phase 6")

    sidebar = getattr(st, "sidebar", st)
    if hasattr(sidebar, "title"):
        sidebar.title("Configuration")
    else:
        st.markdown("## Configuration")
    simulate_enabled = (
        sidebar.checkbox("Enable Simulations", value=True)
        if hasattr(sidebar, "checkbox")
        else st.checkbox("Enable Simulations", value=True)
    )
    design_depth = (
        sidebar.selectbox(
            "Design Depth",
            options=["Low", "Medium", "High"],
            index=0,
            help="Controls how detailed the agent outputs will be.",
        )
        if hasattr(sidebar, "selectbox")
        else st.selectbox(
            "Design Depth",
            options=["Low", "Medium", "High"],
            index=0,
            help="Controls how detailed the agent outputs will be.",
        )
    )
    st.session_state["simulate_enabled"] = simulate_enabled
    st.session_state["design_depth"] = design_depth

    # 1. Get the user’s idea
    idea = st.text_input("🧠 Enter your project idea:")
    if not idea:
        st.info("Please describe an idea to get started.")
        st.stop()
    # Check for similar past projects in memory
    similar_ideas = memory_manager.find_similar_ideas(idea)
    if similar_ideas:
        st.info("Found similar past projects: " + ", ".join(similar_ideas))

    # 2. Generate the role→task plan
    if st.button("1⃣ Generate Research Plan"):
        logging.info(f"User generated plan for idea: {idea}")
        try:
            with st.spinner("📝 Planning..."):
                logging.debug("Planner start")
                raw_plan = agents["Planner"].run(idea, "Break down the project into role-specific tasks")
                logging.debug(f"Raw plan: {raw_plan}")
                if not isinstance(raw_plan, dict):
                    logging.error(f"Planner returned unexpected format: {raw_plan}")
                    st.error("Plan generation failed – received an unexpected response format.")
                    st.stop()
                # keep only keys that have a matching agent
                plan = {role: task for role, task in raw_plan.items() if role in agents}
                dropped = [r for r in raw_plan if r not in agents]
                logging.debug(f"Filtered plan: {plan}, dropped roles: {dropped}")
                if dropped:
                    st.warning(f"Dropped unrecognized roles: {', '.join(dropped)}")
            st.session_state["plan"] = plan
            # Log the plan generation step
            safe_log_step(st.session_state["project_id"], "Planner", "Output", "Plan generated", success=True)
        except openai.OpenAIError as e:
            logging.exception("OpenAI error during plan generation: %s", e)
            st.error("Planning failed: Unable to generate plan. Please check your API key or try again later.")
            st.write("Plan generation failed:", e)
        except json.JSONDecodeError as e:
            logging.exception("JSON decode error during plan generation: %s", e)
            st.error("Planning failed: Plan generation output was not understood – the AI did not return a proper plan.")
            st.write("Plan generation failed:", e)
        except Exception as e:
            logging.exception("Unexpected error during plan generation: %s", e)
            st.error("Planning failed: An unexpected error occurred.")
            st.write("Plan generation failed:", e)

    # Display the plan if it exists in session state
    if "plan" in st.session_state:
        st.subheader("Project Plan (Role → Task)")
        st.json(st.session_state["plan"])

        # 3. Execute each specialist agent (with optional refinement rounds, simulations, and design depth)
        refinement_rounds = st.slider("🔁 Refinement Rounds", 1, 3, value=1)
        simulate_enabled = st.session_state.get("simulate_enabled", True)
        design_depth = st.session_state.get("design_depth", "Low")
        re_run_simulations = (
            st.checkbox("Re-run simulations after each refinement round", value=False)
            if simulate_enabled
            else False
        )

        if st.button("2⃣ Run All Domain Experts"):
            logging.info(
                f"Running domain experts with refinement_rounds={refinement_rounds}, "
                f"design_depth={design_depth}, simulate_enabled={simulate_enabled}"
            )
            answers = {}
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
                        # Include memory context if similar projects found
                        if similar_ideas:
                            context = memory_manager.get_project_summaries(similar_ideas)
                            prompt_base = agent.user_prompt_template.format(idea=idea, task=task)
                            # Append design depth instructions to the prompt base
                            depth = design_depth.capitalize()
                            if depth == "High":
                                prompt_base += (
                                    "\n\n**Design Depth: High** – Include all relevant component-level details, diagrams, and trade-off analysis."
                                )
                            elif depth == "Low":
                                prompt_base += (
                                    "\n\n**Design Depth: Low** – Provide only a high-level summary with minimal detail."
                                )
                            else:  # Medium
                                prompt_base += (
                                    "\n\n**Design Depth: Medium** – Provide a moderate level of detail with key diagrams and justifications."
                                )
                            prompt_with_memory = f"{context}\n\n{prompt_base}" if context else prompt_base
                            import openai
                            response = openai.chat.completions.create(
                                model=agent.model,
                                messages=[
                                    {"role": "system", "content": agent.system_message},
                                    {"role": "user", "content": prompt_with_memory},
                                ]
                            )
                            result = response.choices[0].message.content.strip()
                        else:
                            # Use BaseAgent.run with design_depth parameter
                            result = agent.run(idea, task, design_depth=design_depth)
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
                            "chemical" if any(term in result.lower() for term in ["chemical", "chemistry", "compound", "reaction", "material"]) else "thermal"
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
                        safe_log_step(st.session_state["project_id"], role, "Output", f"Failed {fail_desc}", success=False)
                        # Attempt up to 2 refinements based on failed criteria
                        for attempt in range(1, 3):  # attempt = 1 for first retry, 2 for second retry
                            # Prepare feedback context with failed criteria
                            feedback = ""
                            if failed_list:
                                feedback = f"The simulation indicates failure in: {', '.join(failed_list)}. Please address these issues in the design."
                            # Construct messages to re-run agent with feedback
                            try:
                                import openai
                                revised_response = openai.chat.completions.create(
                                    model=agent.model,
                                    messages=[
                                        {"role": "system", "content": agent.system_message},
                                        {"role": "user", "content": agent.user_prompt_template.format(idea=idea, task=task)},
                                        {"role": "assistant", "content": result},
                                        {"role": "user", "content": feedback if feedback else "The design did not meet some requirements; please refine the proposal."}
                                    ]
                                )
                                new_result = revised_response.choices[0].message.content.strip()
                            except Exception as e:
                                new_result = result  # if the re-run fails, keep the last result
                            # Run simulation again on the revised output
                            new_metrics = simulation_agent.sim_manager.simulate(sim_type, new_result)
                            if new_metrics.get("pass", True):
                                # Success on retry
                                result = new_result
                                # Log successful retry attempt
                                safe_log_step(st.session_state["project_id"], role, f"Retry {attempt}", "Passed Simulation", success=True)
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
                                result = new_result  # update result to the latest attempt for potential display
                                # Log the failed retry attempt
                                safe_log_step(st.session_state["project_id"], role, f"Retry {attempt}", f"Failed {fail_desc}", success=False)
                                if attempt == 2:
                                    # After 2 retries (total 3 attempts including initial) still failing
                                    st.error(f"{role} could not meet simulation constraints after 2 attempts. Halting execution.")
                                    # Log halting scenario
                                    safe_log_step(st.session_state["project_id"], role, "Abort", "Simulation constraints unmet after 2 retries", success=False)
                                    st.stop()
                        # If loop exited without break, it means we exhausted retries and handled stop.
                        # If broke out (success), 'result' is updated and logged.
                    else:
                        # Simulation passed on first try
                        safe_log_step(st.session_state["project_id"], role, "Output", "Passed Simulation", success=True)
                        # Append simulation metrics to the output if no further refinement rounds
                        if refinement_rounds == 1:
                            sim_text = simulation_agent.run_simulation(role, result)
                            if sim_text:
                                result = f"{result}\n\n{sim_text}"
                else:
                    # Simulations not enabled or result is an error
                    # Log the output as completed (success=True by default if no simulation)
                    if not result.startswith("❌"):
                        safe_log_step(st.session_state["project_id"], role, "Output", "Completed", success=True)
                    else:
                        safe_log_step(st.session_state["project_id"], role, "Output", "Failed to generate", success=False)

                answers[role] = result

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
                            agents["CTO"], agents["Research Scientist"],
                            idea, answers["CTO"], answers["Research Scientist"]
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
                                other_outputs = {other_role: ans for other_role, ans in answers.items() if other_role != role}
                                refined_output = refine_agent_output(agent, idea, task, answers.get(role, ""), other_outputs)
                            except Exception as e:
                                refined_output = f"❌ {role} refinement failed: {e}"
                        new_answers[role] = refined_output
                    answers = new_answers
                # After all refinement rounds, append simulation results if enabled (re-run simulations for final outputs)
                if simulate_enabled:
                    for role, output in answers.items():
                        sim_text = SimulationAgent().run_simulation(role, output) if re_run_simulations or True else ""
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

    # 4. Synthesize final proposal
    if "answers" in st.session_state:
        if st.button("3⃣ Compile Final Proposal"):
            logging.info("User compiled final proposal")
            with st.spinner("🚀 Synthesizing final R&D proposal..."):
                try:
                    final_doc = compose_final_proposal(
                        idea,
                        st.session_state["answers"],
                        include_simulations=st.session_state.get("simulate_enabled", True),
                    )
                except Exception as e:
                    st.error(f"Synthesizer failed: {e}")
                    st.stop()
                try:
                    memory_manager.store_project(idea, st.session_state.get("plan", {}), st.session_state["answers"], final_doc)
                except Exception as e:
                    st.warning(f"Could not save project: {e}")
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

    # Sidebar Audit Trail viewer
    if "project_id" in st.session_state:
        logs = audit_logger.get_logs(st.session_state["project_id"])
        if logs:
            with st.sidebar.expander("Audit Trail", expanded=False):
                for entry in logs:
                    symbol = "✓" if entry.get("success", True) else "✗"
                    st.write(f"[{symbol}] {entry['role']} {entry['step_type']} – {entry['content']}")


