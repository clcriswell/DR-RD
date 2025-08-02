import streamlit as st
from agents.planner_agent import PlannerAgent
from agents.cto_agent import CTOAgent
from agents.research_scientist_agent import ResearchScientistAgent
from agents.engineer_agent import EngineerAgent
from agents.qa_agent import QAAgent
from agents.regulatory_agent import RegulatoryAgent
from agents.patent_agent import PatentAgent
from agents.documentation_agent import DocumentationAgent
from agents.synthesizer import compose_final_proposal
from memory.memory_manager import MemoryManager
from collaboration import agent_chat
from utils.refinement import refine_agent_output
from simulation.simulation_manager import SimulationManager
from agents.simulation_agent import SimulationAgent

# --- Instantiate Agents ---
agents = {
    "Planner": PlannerAgent(),
    "CTO": CTOAgent(),
    "Research Scientist": ResearchScientistAgent(),
    "Engineer": EngineerAgent(),
    "QA Specialist": QAAgent(),
    "Regulatory Specialist": RegulatoryAgent(),
    "Patent Specialist": PatentAgent(),
    "Documentation Specialist": DocumentationAgent(),
}

# Initialize persistent memory manager
memory_manager = MemoryManager()

# --- Streamlit UI ---
st.set_page_config(page_title="DR-RD Phase 4: Simulated Multi-Agent R&D", layout="wide")
st.title("DR-RD AI R&D Engine — Phase 4")

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
    with st.spinner("📝 Planning..."):
        try:
            raw_plan = agents["Planner"].run(idea, "Break down the project into role-specific tasks")
            # keep only keys that have a matching agent
            plan = {role: task for role, task in raw_plan.items() if role in agents}
            dropped = [r for r in raw_plan if r not in agents]
            if dropped:
                st.warning(f"Dropped unrecognized roles: {', '.join(dropped)}")
        except Exception as e:
            st.error(f"Planner failed: {e}")
            st.stop()
    st.subheader("Project Plan (Role → Task)")
    st.json(plan)
    st.session_state["plan"] = plan

# 3. Execute each specialist agent (with optional refinement rounds and simulations)
if "plan" in st.session_state:
    refinement_rounds = st.slider("🔁 Refinement Rounds", 1, 3, value=1)
    # Simulation options
    simulate_enabled = st.checkbox("Enable Simulations", value=False)
    re_run_simulations = st.checkbox("Re-run simulations after each refinement round", value=False) if simulate_enabled else False

    if st.button("2⃣ Run All Domain Experts"):
        answers = {}
        simulation_agent = SimulationAgent() if simulate_enabled else None

        # Initial execution by all expert agents
        for role, task in st.session_state["plan"].items():
            agent = agents.get(role)
            if not agent:
                st.warning(f"No agent registered for role: {role}")
                continue
            with st.spinner(f"🤖 {role} working..."):
                try:
                    # Include memory context if similar projects found
                    if similar_ideas:
                        context = memory_manager.get_project_summaries(similar_ideas)
                        prompt = agent.user_prompt_template.format(idea=idea, task=task)
                        prompt_with_memory = f"{context}\n\n{prompt}" if context else prompt
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
                        result = agent.run(idea, task)
                except Exception as e:
                    result = f"❌ {role} failed: {e}"
            # Append simulation results if enabled and no further refinement rounds will modify this output
            if simulate_enabled and refinement_rounds == 1:
                sim_text = simulation_agent.run_simulation(role, result)
                if sim_text:
                    result = f"{result}\n\n{sim_text}"
            answers[role] = result

            # Display initial outputs immediately if no refinement rounds selected
            if refinement_rounds == 1:
                st.markdown(f"---\n### {role} Output")
                st.markdown(answers[role])
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
                        st.markdown(f"---\n### CTO Output (Revised after collaboration)")
                        if simulate_enabled:
                            sim_cto = simulation_agent.run_simulation("CTO", updated_cto)
                            if sim_cto:
                                updated_cto = f"{updated_cto}\n\n{sim_cto}"
                                answers["CTO"] = updated_cto
                        st.markdown(updated_cto)
                        st.markdown(f"---\n### Research Scientist Output (Revised after collaboration)")
                        if simulate_enabled:
                            sim_rs = simulation_agent.run_simulation("Research Scientist", updated_rs)
                            if sim_rs:
                                updated_rs = f"{updated_rs}\n\n{sim_rs}"
                                answers["Research Scientist"] = updated_rs
                        st.markdown(updated_rs)
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
                st.markdown(f"---\n### {role} Output (Refined)")
                st.markdown(output)
            st.session_state["answers"] = answers

# 4. Synthesize final proposal
if "answers" in st.session_state:
    if st.button("3⃣ Compile Final Proposal"):
        with st.spinner("🚀 Synthesizing final R&D proposal..."):
            try:
                final_doc = compose_final_proposal(idea, st.session_state["answers"], include_simulations=simulate_enabled)
            except Exception as e:
                st.error(f"Synthesizer failed: {e}")
                st.stop()
            try:
                memory_manager.store_project(idea, st.session_state.get("plan", {}), st.session_state["answers"], final_doc)
            except Exception as e:
                st.warning(f"Could not save project: {e}")
        st.subheader("📖 Integrated R&D Proposal")
        st.markdown(final_doc)
