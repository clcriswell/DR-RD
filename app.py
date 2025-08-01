import json, os, streamlit as st, openai

# ---- Streamlit config & key handling ----
st.set_page_config(page_title="AI R&D Center", page_icon="🔬")
if "plan" not in st.session_state:
    st.session_state["plan"] = None
if "obfuscated" not in st.session_state:
    st.session_state["obfuscated"] = None

api_key = (
    st.secrets.get("OPENAI_API_KEY")
    or os.getenv("OPENAI_API_KEY")
    or st.sidebar.text_input("Enter your OpenAI API key", type="password")
)
if not api_key:
    st.stop()
openai.api_key = api_key

# ---- UI ----
st.title("🔬 AI Research & Development Center")

idea = st.text_area(
    "Your idea or goal",
    height=150,
    placeholder="e.g. lightweight, heat-resistant material for Mars landers",
)

# ---- 1. Creation Planner ----
if st.button("Generate Task Plan") and idea.strip():
    with st.spinner("Planning…"):
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert R&D planner who divides "
                               "complex projects into domain-specific tasks."
                },
                {
                    "role": "user",
                    "content": (
                        f"Project goal: {idea}\n\nReturn a pure JSON object mapping "
                        "each domain (Physics, Chemistry, Material Science and "
                        "Engineering, Chemical Engineering, Mechanical Engineering, "
                        "Electrical and Computer Engineering, Aerospace Engineering, "
                        "Civil and Environmental Engineering, Nuclear Engineering, "
                        "Industrial and Systems Engineering) to one or two short, "
                        "imperative research tasks."
                    )
                },
            ],
        )
    st.session_state.plan = json.loads(resp.choices[0].message.content)
    st.session_state.obfuscated = None  # reset downstream
    st.success("Creation Planner output:")
    st.json(st.session_state.plan)

# ---- 2. Obfuscator ----
if st.session_state.plan:
    from agents.obfuscator import obfuscate_task
    if st.button("Run Obfuscator"):
        with st.spinner("Obfuscating…"):
            st.session_state.obfuscated = {
                d: obfuscate_task(d, t)
                for d, t in st.session_state.plan.items()
            }
    if st.session_state.obfuscated:
        st.subheader("Original ➜ Obfuscated")
        for d in st.session_state.plan:
            st.markdown(f"**{d}**")
            st.write("• Original:", st.session_state.plan[d])
            st.write("• Obfuscated:", st.session_state.obfuscated[d])
            st.markdown("---")

# ---- 3. Query Router ----
if st.session_state.obfuscated:
    from agents.router import route
    if st.button("Run Query Router"):
        with st.spinner("Contacting external services…"):
            answers = {
                d: route(d, p) for d, p in st.session_state.obfuscated.items()
            }
        st.success("Results")
        for d, ans in answers.items():
            st.markdown(f"**{d}**")
            st.write(ans)
            st.markdown("---")
