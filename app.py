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

# --- Streamlit UI ---
st.set_page_config(page_title="DR-RD Phase 2: Multi-Agent R&D", layout="wide")
st.title("DR-RD AI R&D Engine — Phase 2b")

# 1. Get the user’s idea
idea = st.text_input("🧠 Enter your project idea:")
if not idea:
    st.info("Please describe an idea to get started.")
    st.stop()

# 2. Generate the role→task plan
if st.button("1⃣ Generate Research Plan"):
    with st.spinner("📝 Planning..."):
        try:
            plan = agents["Planner"].run(
                idea, "Break down the project into role-specific tasks"
            )
        except Exception as e:
            st.error(f"Planner failed: {e}")
            st.stop()
    st.subheader("Project Plan (Role → Task)")
    st.json(plan)
    st.session_state["plan"] = plan

# 3. Execute each specialist agent
if "plan" in st.session_state:
    if st.button("2⃣ Run All Domain Experts"):
        answers = {}
        for role, task in st.session_state["plan"].items():
            agent = agents.get(role)
            if not agent:
                st.warning(f"No agent registered for role: {role}")
                continue
            with st.spinner(f"🤖 {role} working..."):
                try:
                    result = agent.run(idea, task)
                except Exception as e:
                    result = f"❌ {role} failed: {e}"
                answers[role] = result
                st.markdown(f"---\n### {role} Output")
                st.markdown(result)
        st.session_state["answers"] = answers

# 4. Synthesize final proposal
if "answers" in st.session_state:
    if st.button("3⃣ Compile Final Proposal"):
        with st.spinner("🚀 Synthesizing final R&D proposal..."):
            try:
                final_doc = compose_final_proposal(idea, st.session_state["answers"])
            except Exception as e:
                st.error(f"Synthesizer failed: {e}")
                st.stop()
        st.subheader("📖 Integrated R&D Proposal")
        st.markdown(final_doc)
