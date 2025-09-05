import json
import streamlit as st
from core.orchestrator import compose_final_proposal

def test_open_issues_section_in_report():
    st.session_state.clear()
    valid = {"role": "CTO", "task": "t", "findings": "x", "risks": [], "next_steps": [], "sources": []}
    st.session_state["answers_raw"] = {"CTO": [json.dumps(valid)]}
    placeholder = {"role": "CTO", "task": "t", "findings": "TODO", "risks": "TODO", "next_steps": "TODO", "sources": []}
    st.session_state["open_issues"] = [{"task_id": "T1", "role": "CTO", "result": placeholder, "title": "t"}]
    report = compose_final_proposal("idea", {"CTO": json.dumps(valid)})
    assert "## Open Issues" in report
    assert "T1" in report
