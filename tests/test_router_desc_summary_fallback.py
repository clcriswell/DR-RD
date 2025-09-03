import streamlit as st

from core.router import route_task


def test_router_uses_desc_or_summary_and_fallback():
    st.session_state.clear()
    t1 = {"id": "1", "title": "Check", "description": "market trends"}
    role1, _, _, _ = route_task(t1)
    assert role1 == "Marketing Analyst"

    t2 = {"id": "2", "title": "Review", "summary": "regulatory filings"}
    role2, _, _, _ = route_task(t2)
    assert role2 == "Regulatory"

    t3 = {"id": "3", "title": "Misc", "summary": "nothing", "role": "Unknown"}
    role3, _, _, routed = route_task(t3)
    assert role3 == "Dynamic Specialist"
    assert routed["title"] == "Misc"
    assert len(st.session_state.get("routing_report", [])) == 3

