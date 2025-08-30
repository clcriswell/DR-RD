"""Dataset evaluation runner."""

import pandas as pd
import streamlit as st
from pathlib import Path

from utils.eval import datasets, runner

st.set_page_config(page_title="Evaluation", page_icon=":material/analytics:")

st.title("Evaluation")

DATASET_DIR = Path("eval/datasets")
files = sorted(DATASET_DIR.glob("*.jsonl")) + sorted(DATASET_DIR.glob("*.csv"))
file_names = [f.name for f in files]
selected = st.selectbox("Dataset", file_names)
use_llm = st.checkbox("Use LLM rubric", help="Costs tokens")

if st.button("Run evaluation"):
    path = DATASET_DIR / selected
    if path.suffix == ".jsonl":
        items = datasets.normalize(datasets.load_jsonl(str(path)))
    else:
        items = datasets.normalize(datasets.load_csv(str(path)))
    summary = runner.run_eval(items, use_llm=use_llm)
    st.session_state["eval_summary"] = summary

summary = st.session_state.get("eval_summary")
if summary:
    st.write(f"Last run: {summary['out_dir']}")
    st.dataframe(pd.DataFrame(summary["rows"]))
    with open(summary["csv"], "r", encoding="utf-8") as f:
        st.download_button("Download CSV", f.read(), file_name="scoreboard.csv")
    with open(summary["md"], "r", encoding="utf-8") as f:
        st.download_button("Download Markdown", f.read(), file_name="scoreboard.md")
