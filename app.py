import json
import os
import streamlit as st
import openai

# ---------- Streamlit page config ----------
st.set_page_config(
    page_title="AI R&D Center",
    page_icon="🔬",
    layout="centered"
)

# ---------- API key handling ----------
# 1) Prefer Streamlit secrets (for Streamlit Cloud)
# 2) Fallback to an env var
# 3) Allow user paste-in (dev only)
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("Enter your OpenAI API key", type="password")
if not api_key:
    st.stop()        # Don’t run until key provided
openai.api_key = api_key

# ---------- UI ----------
st.title("🔬 AI Research & Development Center")
st.markdown(
    "Enter a **high-level idea**. Step 1 will run the *Creation Planner* "
    "to break your goal into domain-specific research tasks."
)

idea = st.text_area("Your idea or goal", height=150, placeholder="e.g. a lightweight, heat-resistant material for Mars landers")
run_btn = st.button("Generate Task Plan")

# ---------- Planner logic ----------
if run_btn and idea.strip():
    with st.spinner("Thinking 🤔 …"):
        response = openai.chat.completions.create(
            model="gpt-4o-mini",   # or "gpt-4o"
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert R&D planner who divides complex projects "
                        "into domain-specific research tasks."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Project goal: {idea}\n\n"
                        "Return a **pure JSON** object mapping each of the following "
                        "domains to **one or two key research questions or tasks**:\n"
                        " - Physics\n - Chemistry\n - Material Science and Engineering\n"
                        " - Chemical Engineering\n - Mechanical Engineering\n"
                        " - Electrical and Computer Engineering\n - Aerospace Engineering\n"
                        " - Civil and Environmental Engineering\n - Nuclear Engineering\n"
                        " - Industrial and Systems Engineering\n\n"
                        "Use short, imperative task phrases."
                    )
                }
            ]
        )

    raw = response.choices[0].message.content
    try:
        plan = json.loads(raw)
    except json.JSONDecodeError:
        st.error("Planner did not return valid JSON. Raw output shown below:")
        st.code(raw)
        st.stop()

    st.success("Creation Planner output:")
    st.json(plan)

    # ---------- NEW: Obfuscate each task ----------
    st.header("🔒 Prompt Obfuscation")
    obfuscated = {}
    if st.button("Run Obfuscator"):
        with st.spinner("Obfuscating prompts…"):
            from agents.obfuscator import obfuscate_task  # local import to avoid circulars
            for domain, task in plan.items():
                try:
                    obfuscated[domain] = obfuscate_task(domain, task)
                except Exception as e:
                    obfuscated[domain] = f"(error: {e})"

        st.subheader("Original ➜ Obfuscated")
        for d in plan:
            st.markdown(f"**{d}**")
            st.write("• Original:", plan[d])
            st.write("• Obfuscated:", obfuscated[d])
            st.markdown("---")

        st.info(
            "✅ **Next step preview**: Each obfuscated prompt will be routed "
            "through the API Query Router (IP rotation, header randomization, etc.)."
        )
