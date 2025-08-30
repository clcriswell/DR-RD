"""Thin Streamlit UI for DR-RD."""

import io
import json
import logging
import time
from pathlib import Path

import fitz
import streamlit as st
from markdown_pdf import MarkdownPdf, Section

st.set_page_config(
    page_title="DR-RD",
    page_icon=":material/science:",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "DR-RD — AI R&D Workbench"},
)

from app.ui.a11y import inject_accessibility_baseline, live_region_container

inject_accessibility_baseline()
live_region_container()

from app.ui import components
from app.ui.sidebar import render_sidebar
from app.ui import survey
from config.agent_models import AGENT_MODEL_MAP
import config.feature_flags as ff
from core.agents.unified_registry import build_agents_unified
from utils.run_config import to_orchestrator_kwargs
from utils.telemetry import log_event
from utils.errors import make_safe_error
from utils.run_id import new_run_id
from utils.paths import ensure_run_dirs
from utils.runs import create_run_meta, complete_run_meta

WRAP_CSS = """
pre, code {
    white-space: pre-wrap;
    word-break: break-word;
    overflow-wrap: anywhere;
}
"""

logger = logging.getLogger(__name__)


CONFIG_PATH = Path(".dr_rd/config.json")


def load_ui_config() -> dict:
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_ui_config(data: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _apply_stored_defaults() -> None:
    cfg = load_ui_config()
    for key, val in cfg.items():
        st.session_state.setdefault(key, val)


def get_agents():
    mapping = AGENT_MODEL_MAP
    default = mapping.get("DEFAULT") or "gpt-4o-mini"
    return build_agents_unified(mapping, default)


def main() -> None:
    from core.orchestrator import compose_final_proposal, execute_plan, generate_plan

    _apply_stored_defaults()
    survey.render_usage_panel()
    components.help_once(
        "first_run_tip",
        "After you start, the app plans, executes tasks, then synthesizes a report.",
    )

    cfg = render_sidebar()
    submitted = st.button("Start run", type="primary")
    if not submitted or not cfg.idea.strip():
        return

    kwargs = to_orchestrator_kwargs(cfg)
    ff.RAG_ENABLED = kwargs["rag"]
    ff.ENABLE_LIVE_SEARCH = kwargs["live"]

    run_id = new_run_id()
    ensure_run_dirs(run_id)
    create_run_meta(run_id, mode=kwargs["mode"], idea_preview=kwargs["idea"][:120])
    st.session_state["run_id"] = run_id
    st.query_params["run_id"] = run_id
    log_event(
        {
            "event": "run_created",
            "run_id": run_id,
            "mode": kwargs["mode"],
            "rag": kwargs["rag"],
            "live": kwargs["live"],
            "budget": kwargs["budget"],
        }
    )

    progress = components.step_progress(3)
    progress(0, "Starting run")

    current_phase = "start"
    current_box = None

    try:
        start = time.time()
        current_phase = "plan"
        with components.stage_status("Planning…") as box:
            current_box = box
            tasks = generate_plan(kwargs["idea"])
            box.update(label="Planning complete", state="complete")
        log_event({
            "event": "step_completed",
            "run_id": run_id,
            "stage": "plan",
            "duration": time.time() - start,
        })
        progress(1, "Plan ready")

        start = time.time()
        current_phase = "exec"
        with components.stage_status("Executing…") as box:
            current_box = box
            answers = execute_plan(kwargs["idea"], tasks, agents=get_agents())
            box.update(label="Execution complete", state="complete")
        log_event({
            "event": "step_completed",
            "run_id": run_id,
            "stage": "exec",
            "duration": time.time() - start,
        })
        progress(2, "Execution finished")

        start = time.time()
        current_phase = "synth"
        with components.stage_status("Synthesizing…") as box:
            current_box = box
            final = compose_final_proposal(kwargs["idea"], answers)
            box.update(label="Synthesis complete", state="complete")
        log_event({
            "event": "step_completed",
            "run_id": run_id,
            "stage": "synth",
            "duration": time.time() - start,
        })
        progress(3, "Run complete")
        st.markdown(final)
        st.session_state["run_report"] = final
        st.query_params.update({"run_id": run_id})
        complete_run_meta(run_id, status="success")
        log_event({"event": "run_completed", "run_id": run_id, "status": "success"})
        st.markdown("[Open Trace](./Trace)")
        st.caption("Use the Trace page to inspect step details.")
        survey.maybe_prompt_after_run(run_id)
    except Exception as e:  # pragma: no cover - UI display
        if current_box is not None:
            current_box.update(label="Error", state="error")
        err = make_safe_error(
            e, run_id=run_id, phase=current_phase, step_id=None
        )
        complete_run_meta(run_id, status="error")
        log_event({"event": "run_completed", "run_id": run_id, "status": "error"})
        log_event(
            {
                "event": "error_shown",
                "support_id": err.support_id,
                "kind": err.kind,
                "where": err.context.get("phase"),
                "run_id": err.context.get("run_id"),
                "tech": err.tech_message[:200],
            }
        )
        components.error_banner(err)
        r1, r2 = st.columns([1, 1])
        with r1:
            retry = st.button("Retry run", type="primary", use_container_width=True)
        with r2:
            open_trace = st.button("Open trace", use_container_width=True)
        if retry:
            st.query_params["retry_of"] = err.context.get("run_id") or ""
            st.rerun()
        if open_trace:
            st.query_params["run_id"] = err.context.get("run_id") or ""
            st.switch_page("pages/10_Trace.py")


def generate_pdf(markdown_text):
    if isinstance(markdown_text, dict):
        markdown_text = markdown_text.get("document", "")
    pdf = MarkdownPdf(toc_level=2)
    pdf.add_section(Section(markdown_text), user_css=WRAP_CSS)
    pdf.writer.close()
    pdf.out_file.seek(0)
    try:
        doc = fitz.Story.add_pdf_links(pdf.out_file, pdf.hrefs)
    except Exception as e:  # pragma: no cover - optional
        logging.warning(f"Failed to add PDF links: {e}")
        pdf.out_file.seek(0)
        doc = fitz.open(stream=pdf.out_file, filetype="pdf")
    doc.set_metadata(pdf.meta)
    if not doc.get_toc():
        doc.set_toc([[1, "Document", 1]])
    out = io.BytesIO()
    doc.save(out)
    doc.close()
    return out.getvalue()
