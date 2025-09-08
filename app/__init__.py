"""Thin Streamlit UI for DR-RD."""

# ruff: noqa: E402, F401, F821

from app.logging_setup import init_gcp_logging
from dr_rd.config import env as _env  # noqa: F401

init_gcp_logging()

import io
import json
import logging
import os
import time

import fitz
import streamlit as st
from markdown_pdf import MarkdownPdf, Section

from dr_rd.config.env import get_env
from dr_rd.telemetry.api_call_log import APICallLogger
from dr_rd.telemetry import loggers as api_loggers
from utils.i18n import missing_keys, set_locale
from utils.i18n import tr as t
from utils.session_store import get_session_id, init_stores  # noqa: F401

st.set_page_config(
    page_title=t("app_title"),
    page_icon=":material/science:",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "DR-RD — AI R&D Workbench"},
)

from dataclasses import asdict

from app.ui.a11y import aria_live_region, inject, main_start
from app.ui.command_palette import open_palette
from core.orchestrator import compose_final_proposal, execute_plan, generate_plan
from utils import consent as _consent
from utils import safety as safety_utils
from utils import session_guard, trace_writer
from utils.cancellation import CancellationToken
from utils.experiments import assign, exposure, force_from_params
from utils.flags import is_enabled
from utils.telemetry import (
    demo_completed,
    demo_started,
    exp_overridden,
    log_event,
    run_cancel_requested,
    run_cancelled,
    run_duplicate_detected,
    run_lock_acquired,
    run_lock_released,
    run_start_blocked,
    timeout_hit,
)
from utils.usage import Usage
from utils.user_id import get_user_id

inject()
main_start()
aria_live_region()

run_store, view_store = init_stores()

st.session_state.setdefault("active_run", None)
st.session_state.setdefault("submit_token", None)

_c = _consent.get()
if _c is None:
    try:

        @st.dialog("Privacy & consent")
        def _dlg():
            st.write(
                "Allow anonymous telemetry and optional in app surveys? You can change this anytime in Privacy settings."
            )
            tel = st.checkbox("Allow telemetry", value=True)
            srv = st.checkbox("Allow surveys", value=True)
            if st.button("Save choices", type="primary"):
                _consent.set(telemetry=tel, surveys=srv)
                log_event(
                    {
                        "event": "consent_changed",
                        "telemetry": bool(tel),
                        "surveys": bool(srv),
                    }
                )
                st.rerun()

        _dlg()
    except Exception:
        # Fallback inline block if dialogs unavailable
        with st.expander("Privacy & consent", expanded=True):
            tel = st.checkbox("Allow telemetry", value=True, key="c_tel")
            srv = st.checkbox("Allow surveys", value=True, key="c_srv")
            if st.button("Save choices", key="c_save"):
                _consent.set(telemetry=tel, surveys=srv)
                log_event(
                    {
                        "event": "consent_changed",
                        "telemetry": bool(tel),
                        "surveys": bool(srv),
                    }
                )
                st.rerun()

params = dict(st.query_params)
uid = get_user_id()
forced_nav = force_from_params(params, "exp_trace_nav")
if forced_nav:
    exp_overridden("exp_trace_nav", forced_nav)
nav_variant = forced_nav or assign(uid, "exp_trace_nav")[0]
exposure(log_event, uid, "exp_trace_nav", nav_variant, run_id=params.get("run_id"))
if forced_nav:
    st.caption("Experiment override active.")

active = st.session_state.get("active_run")
qp_run = params.get("run_id")
if qp_run and not active and session_guard.is_locked(qp_run):
    st.info(f"Another tab may be watching run {qp_run}.")
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Take over", key="takeover"):
            tok = session_guard.new_token()
            session_guard.acquire(qp_run, tok)
            st.session_state["active_run"] = {"run_id": qp_run, "token": tok, "status": "running"}
            st.session_state["submit_token"] = tok
            run_duplicate_detected(qp_run)
    with c2:
        st.markdown(f"[Open Trace](./Trace?run_id={qp_run})")

if not st.session_state.get("_onboard_shown", False):
    try:

        @st.dialog(t("welcome_title"))
        def _welcome():
            st.write(t("welcome_body"))
            st.caption(t("run_help"))
            st.button("Got it", key="welcome_ok")

        _welcome()
    except Exception:
        with st.expander(t("welcome_title"), expanded=True):
            st.write(t("welcome_body"))
            st.caption(t("run_help"))
    st.session_state["_onboard_shown"] = True
    log_event({"event": "onboarding_shown"})

from dataclasses import replace
from urllib.parse import urlencode

import config.feature_flags as ff
from app.ui import components, meter, survey
from app.ui.sidebar import render_sidebar
from config.agent_models import AGENT_MODEL_MAP
from core.agents.unified_registry import build_agents_unified
from utils import bundle
from utils.env_snapshot import capture_env
from utils.errors import make_safe_error
from utils.notify import Note
from utils.notify import dispatch as notify_dispatch
from utils.paths import artifact_path, ensure_run_dirs, run_root, write_bytes, write_text
from utils.prefs import load_prefs
from utils.query_params import (
    QP_APPLIED_KEY,
    decode_config,
    encode_config,
    merge_into_defaults,
    view_state_from_params,
)
from utils.run_config import (
    RunConfig,
    defaults,
    to_orchestrator_kwargs,
    to_session,
)
from utils.run_config_io import to_lockfile
from utils.run_id import new_run_id
from utils.runs import complete_run_meta, create_run_meta
from utils.telemetry import notification_sent

WRAP_CSS = """
pre, code {
    white-space: pre-wrap;
    word-break: break-word;
    overflow-wrap: anywhere;
}
"""

logger = logging.getLogger(__name__)


def _apply_prefs() -> dict:
    prefs = load_prefs()
    lang = prefs["ui"].get("language", "en")
    set_locale(lang)
    if not st.session_state.get("_i18n_missing_logged"):
        miss = missing_keys(lang)
        if miss:
            log_event({"event": "i18n_missing_keys", "lang": lang, "count": len(miss)})
        st.session_state["_i18n_missing_logged"] = True
    if not st.session_state.get("_prefs_applied"):
        to_session(defaults())
        st.session_state.setdefault(
            "show_agent_trace", prefs["ui"].get("show_trace_by_default", True)
        )
        st.session_state["_prefs_applied"] = True
    return prefs


def get_agents():
    mapping = AGENT_MODEL_MAP
    default = mapping.get("DEFAULT") or "gpt-4o-mini"
    return build_agents_unified(mapping, default)


def main() -> None:
    prefs = _apply_prefs()
    origin_run_id = st.query_params.get("origin_run_id")
    if st.session_state.get(QP_APPLIED_KEY) is not True:
        decoded = decode_config(st.query_params)
        rc_defaults = asdict(defaults())
        merged = merge_into_defaults(rc_defaults, decoded)
        extra = {k: merged.pop(k) for k in list(merged.keys()) if k not in rc_defaults}
        adv = merged.get("advanced", {})
        adv.update(extra)
        merged["advanced"] = adv
        to_session(RunConfig(**merged))
        st.session_state[QP_APPLIED_KEY] = True
        if decoded:
            log_event(
                {
                    "event": "config_prefilled_from_url",
                    "fields": {k: len(str(v)) for k, v in decoded.items()},
                }
            )
        view_state = view_state_from_params(st.query_params)
        if view_state["view"] != "run":
            target = {
                "trace": "pages/02_Results.py",
                "reports": "pages/03_Reports.py",
                "history": "pages/04_History.py",
                "settings": "pages/05_Settings.py",
            }.get(view_state["view"])
            if target:
                st.switch_page(target)

    # Command palette controls
    if st.button(
        "⌘K Command palette",
        key="cmd_btn",
        width="content",
        help="Open global search",
    ):
        log_event({"event": "palette_opened"})
        open_palette()

    if st.query_params.get("cmd") == "1":
        log_event({"event": "palette_opened", "source": "qp"})
        open_palette()
        st.query_params.pop("cmd", None)

    act = st.session_state.pop("_cmd_action", None)
    if act:
        if act["action"] == "switch_page":
            st.switch_page(act["params"]["page"])
        elif act["action"] == "set_params":
            st.query_params.update(act["params"])
            st.rerun()
        elif act["action"] == "copy":
            st.code(act["params"]["text"], language=None)
            st.toast("Copied link")
        elif act["action"] == "start_demo":
            st.query_params.update({"mode": "demo", "view": "run"})
            st.toast("Demo mode selected. Review and start.")
        log_event(
            {
                "event": "palette_executed",
                "kind": act.get("kind"),
                "action": act["action"],
            }
        )

    survey.render_usage_panel()
    components.help_once(
        "first_run_tip",
        t("run_help"),
    )

    if not is_enabled("wizard_form", params=params):
        st.warning("Wizard form disabled")
        st.stop()
    if nav_variant == "top_nav":
        st.caption("Top navigation variant")
    cfg = render_sidebar()
    active_run = st.session_state.get("active_run")
    col_run, col_demo, col_share = st.columns([2, 2, 1])
    with col_run:
        submitted = st.button(
            t("start_run_label"),
            type="primary",
            help=t("start_run_help"),
            disabled=active_run is not None and active_run.get("status") == "running",
        )
    with col_demo:
        demo_submit = st.button(
            "Run demo",
            type="secondary",
            help="Play a recorded run with no cost",
            disabled=active_run is not None and active_run.get("status") == "running",
        )
    with col_share:
        include_adv = st.checkbox(
            t("include_adv_label"), key="share_adv", help=t("include_adv_help")
        )
        if st.button(
            t("share_link_label"),
            key="share_link",
            help=t("share_link_help"),
            disabled=active_run is not None and active_run.get("status") == "running",
        ):
            qp = encode_config(to_orchestrator_kwargs(cfg))
            if not include_adv:
                qp.pop("adv", None)
            url = "./?" + urlencode(qp)
            st.text_input(t("share_link_url_label"), value=url, help=t("share_link_help"))
            log_event(
                {
                    "event": "link_shared",
                    "where": "entry",
                    "included_adv": bool(include_adv),
                }
            )
    if not (submitted or demo_submit) or not cfg.idea.strip():
        return

    if active_run and active_run.get("status") == "running":
        st.warning("Run already in progress")
        run_start_blocked("already_running", active_run.get("run_id"))
        return

    qp_run = st.query_params.get("run_id")
    if qp_run and session_guard.is_locked(qp_run):
        st.info(f"Another tab may be watching run {qp_run}.")
        run_start_blocked("cross_tab", qp_run)
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Resume watching this run", key="resume_existing"):
                tok = session_guard.new_token()
                session_guard.acquire(qp_run, tok)
                st.session_state["active_run"] = {
                    "run_id": qp_run,
                    "token": tok,
                    "status": "running",
                }
                st.session_state["submit_token"] = tok
                run_duplicate_detected(qp_run)
                st.query_params["run_id"] = qp_run
                st.switch_page("pages/02_Results.py")
        with col2:
            if st.button("Start a new run", key="start_new_run"):
                st.query_params.pop("run_id", None)
                st.rerun()
        return

    if demo_submit:
        cfg = replace(cfg, mode="demo")

    kwargs = to_orchestrator_kwargs(cfg)
    # Extract any pinned prompts so they can be recorded with the run metadata.
    prompt_pins = kwargs.get("prompts") or kwargs.get("prompt_pins")
    os.environ["DRRD_PSEUDONYMIZE_TO_MODEL"] = (
        "1" if kwargs.get("pseudonymize_to_model", True) else "0"
    )
    resume_from = st.query_params.pop("resume_from", None)
    if resume_from:
        kwargs["resume_from"] = resume_from
    qp = encode_config(kwargs)
    st.query_params.update(qp)
    log_event({"event": "config_encoded_to_url", "field_count": len(qp)})
    ff.RAG_ENABLED = kwargs["rag"]
    ff.ENABLE_LIVE_SEARCH = kwargs["live"]

    submit_token = session_guard.new_token()
    run_id = new_run_id()
    st.session_state["submit_token"] = submit_token
    st.session_state["active_run"] = {"run_id": run_id, "token": submit_token, "status": "running"}
    session_guard.acquire(run_id, submit_token)
    run_lock_acquired(run_id)
    ensure_run_dirs(run_id)
    st.session_state["run_id"] = run_id
    st.query_params["run_id"] = run_id

    if cfg.mode == "demo":
        demo_started(run_id)
        from utils.run_playback import materialize_run

        outputs = materialize_run(run_id)
        st.session_state["usage"] = Usage()
        st.markdown(outputs["report_md"])
        meter.render_summary(st.session_state["usage"])
        st.session_state["run_report"] = outputs["report_md"]
        if prefs["ui"].get("auto_export_on_completion"):
            try:

                def _read_bytes(rid, name, ext):
                    return artifact_path(rid, name, ext).read_bytes()

                def _list_existing(rid):
                    root = run_root(rid)
                    return [(p.stem, p.suffix.lstrip(".")) for p in root.iterdir() if p.is_file()]

                data = bundle.build_zip_bundle(
                    run_id,
                    [],
                    read_bytes=_read_bytes,
                    list_existing=_list_existing,
                    sanitize=lambda n, e, b: b,
                )
                write_bytes(run_id, "bundle", "zip", data)
            except Exception:
                pass
        st.query_params.update({"run_id": run_id, "view": "trace"})
        demo_completed(run_id)
        if prefs["ui"].get("show_trace_by_default"):
            st.switch_page("pages/02_Results.py")
        else:
            st.markdown("[Open Trace](./Trace)")
            st.caption("Use the Trace page to inspect step details.")
        survey.maybe_prompt_after_run(run_id)
        return

    create_run_meta(
        run_id,
        mode=kwargs["mode"],
        idea_preview=kwargs["idea"][:120],
        prompts=prompt_pins,
    )
    cfg_dict = asdict(cfg)
    if prompt_pins:
        cfg_dict["prompts"] = prompt_pins
    write_text(run_id, "run_config", "lock.json", json.dumps(to_lockfile(cfg_dict)))
    write_text(run_id, "env", "snapshot.json", json.dumps(capture_env()))
    if origin_run_id:
        log_event({"event": "reproduce_started", "run_id": run_id, "origin_run_id": origin_run_id})
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
    st.session_state["budget_limit_usd"] = kwargs.get("budget_limit_usd")
    st.session_state["max_tokens"] = kwargs.get("max_tokens")
    st.session_state["usage"] = Usage()
    st.subheader("Live output")
    _run(run_id, kwargs, prefs, origin_run_id)


def send_note(
    event: str, status: str, run_id: str, kwargs: dict, extra: dict | None = None
) -> None:
    usage = st.session_state.get("usage")
    totals = {
        "tokens": getattr(usage, "total_tokens", None),
        "cost_usd": getattr(usage, "cost_usd", None),
    }
    base = get_env("APP_BASE_URL") or (
        "https://dr-rnd.streamlit.app" if get_env("STREAMLIT_RUNTIME") else "http://localhost:8501"
    )
    url = f"{base}/?view=trace&run_id={run_id}"
    note = Note(
        event=event,
        run_id=run_id,
        status=status,
        mode=kwargs["mode"],
        idea_preview=kwargs["idea"],
        totals=totals,
        url=url,
        extra=extra,
    )
    res = notify_dispatch(note, load_prefs())
    notification_sent(run_id, status, [k for k, v in res.items() if v], any(res.values()))


def _run(run_id: str, kwargs: dict, prefs: dict, origin_run_id: str | None) -> None:
    st.subheader("Live usage")
    live = meter.render_live(
        st.session_state["usage"],
        budget_limit_usd=kwargs.get("budget_limit_usd"),
        token_limit=kwargs.get("max_tokens"),
    )
    if live.get("budget_exceeded") or live.get("token_exceeded"):
        raise RuntimeError("usage_exceeded")
    token = CancellationToken()
    st.session_state[f"cancel_{run_id}"] = token
    deadline_ts = None
    stop = st.button(
        "Stop run",
        key=f"stop_{run_id}",
        type="secondary",
        width="stretch",
    )
    if stop:
        token.cancel()
        run_cancel_requested(run_id)

    progress = components.step_progress(3)
    progress(0, "Starting run")

    current_phase = "start"
    current_box = None
    log_enabled = os.getenv("DRRD_API_CALL_LOG", "true").lower() not in (
        "0",
        "false",
        "no",
    )
    api_logger = APICallLogger(run_id, ensure_run_dirs(run_id), enabled=log_enabled)
    api_loggers.set_api_call_logger(api_logger)

    try:
        start = time.time()
        current_phase = "plan"
        with components.stage_status("Planning…") as box:
            current_box = box
            try:
                tasks = generate_plan(
                    kwargs["idea"],
                    cancel=token,
                    deadline_ts=deadline_ts,
                )
            except ValueError as e:
                box.update(label="Planning failed", state="error")
                reason = str(e)
                msg = {
                    "planner.normalization_zero": f"Planner produced tasks but normalization removed them (run {run_id}).",
                    "planner.no_tasks": f"Planner returned no tasks (run {run_id}).",
                }.get(reason, f"{reason} (run {run_id})")
                st.error(msg)
                return
            box.update(label="Planning complete", state="complete")
        res = safety_utils.check_text(json.dumps(tasks))
        trace_writer.append_step(
            run_id,
            {
                "phase": "planner",
                "summary": tasks,
                "prompt_preview": st.session_state.pop("_last_prompt", None),
                **({"safety": asdict(res)} if res.findings else {}),
            },
        )
        log_event(
            {
                "event": "step_completed",
                "run_id": run_id,
                "stage": "plan",
                "duration": time.time() - start,
            }
        )
        session_guard.mark_heartbeat(run_id)
        live = meter.render_live(
            st.session_state["usage"],
            budget_limit_usd=kwargs.get("budget_limit_usd"),
            token_limit=kwargs.get("max_tokens"),
        )
        if live.get("budget_exceeded") or live.get("token_exceeded"):
            raise RuntimeError("usage_exceeded")
        progress(1, "Plan ready")

        start = time.time()
        current_phase = "exec"
        with components.stage_status("Executing…") as box:
            current_box = box
            try:
                answers = execute_plan(
                    kwargs["idea"],
                    tasks,
                    agents=get_agents(),
                    cancel=token,
                    deadline_ts=deadline_ts,
                )
            except ValueError as e:
                box.update(label="Execution failed", state="error")
                reason = str(e)
                msg = {
                    "no_executable_tasks": f"No executable tasks after routing (run {run_id}).",
                    "No executable tasks after planning/routing": f"No executable tasks after routing (run {run_id}).",
                }.get(reason, f"{reason} (run {run_id})")
                st.error(msg)
                return
            box.update(label="Execution complete", state="complete")
        res = safety_utils.check_text(json.dumps(answers))
        trace_writer.append_step(
            run_id,
            {
                "phase": "executor",
                "summary": answers,
                "prompt_preview": st.session_state.pop("_last_prompt", None),
                **({"safety": asdict(res)} if res.findings else {}),
            },
        )
        log_event(
            {
                "event": "step_completed",
                "run_id": run_id,
                "stage": "exec",
                "duration": time.time() - start,
            }
        )
        session_guard.mark_heartbeat(run_id)
        live = meter.render_live(
            st.session_state["usage"],
            budget_limit_usd=kwargs.get("budget_limit_usd"),
            token_limit=kwargs.get("max_tokens"),
        )
        if live.get("budget_exceeded") or live.get("token_exceeded"):
            raise RuntimeError("usage_exceeded")
        progress(2, "Execution finished")

        start = time.time()
        current_phase = "synth"
        with components.stage_status("Synthesizing…") as box:
            current_box = box
            final = compose_final_proposal(
                kwargs["idea"],
                answers,
                cancel=token,
                deadline_ts=deadline_ts,
            )
            box.update(label="Synthesis complete", state="complete")
        res = safety_utils.check_text(final)
        trace_writer.append_step(
            run_id,
            {
                "phase": "synth",
                "summary": final,
                "prompt_preview": st.session_state.pop("_last_prompt", None),
                **({"safety": asdict(res)} if res.findings else {}),
            },
        )
        log_event(
            {
                "event": "step_completed",
                "run_id": run_id,
                "stage": "synth",
                "duration": time.time() - start,
            }
        )
        session_guard.mark_heartbeat(run_id)
        live = meter.render_live(
            st.session_state["usage"],
            budget_limit_usd=kwargs.get("budget_limit_usd"),
            token_limit=kwargs.get("max_tokens"),
        )
        if live.get("budget_exceeded") or live.get("token_exceeded"):
            raise RuntimeError("usage_exceeded")
        progress(3, "Run complete")
        st.markdown(final)
        meter.render_summary(st.session_state["usage"])
        st.session_state["run_report"] = final
        st.query_params.update({"run_id": run_id, "view": "trace"})
        st.session_state["active_run"]["status"] = "success"
        complete_run_meta(run_id, status="success")
        log_event({"event": "run_completed", "run_id": run_id, "status": "success"})
        send_note("run_completed", "success", run_id, kwargs)
        if origin_run_id:
            log_event(
                {
                    "event": "reproduce_completed",
                    "run_id": run_id,
                    "origin_run_id": origin_run_id,
                    "status": "success",
                }
            )
        if prefs["ui"].get("auto_export_on_completion"):
            try:

                def _read_bytes(rid, name, ext):
                    return artifact_path(rid, name, ext).read_bytes()

                def _list_existing(rid):
                    root = run_root(rid)
                    return [(p.stem, p.suffix.lstrip(".")) for p in root.iterdir() if p.is_file()]

                data = bundle.build_zip_bundle(
                    run_id,
                    [],
                    read_bytes=_read_bytes,
                    list_existing=_list_existing,
                    sanitize=lambda n, e, b: b,
                )
                write_bytes(run_id, "bundle", "zip", data)
            except Exception:
                pass
        if prefs["ui"].get("show_trace_by_default"):
            st.switch_page("pages/02_Results.py")
        else:
            st.markdown("[Open Trace](./Trace)")
            st.caption("Use the Trace page to inspect step details.")
        survey.maybe_prompt_after_run(run_id)
    except ValueError as e:  # pragma: no cover - planner/executor validation
        if current_box is not None:
            current_box.update(label="Error", state="error")
        st.session_state["active_run"]["status"] = "error"
        complete_run_meta(run_id, status="error")
        st.error(
            f"Run {run_id} failed: {e}. Planner must produce non-empty title/summary for each task.",
        )
        return
    except RuntimeError as e:  # pragma: no cover - UI display
        if current_box is not None:
            current_box.update(label="Error", state="error")
        err = make_safe_error(e, run_id=run_id, phase=current_phase, step_id=None)
        st.session_state["active_run"]["status"] = "error"
        complete_run_meta(run_id, status="error")
        log_event({"event": "run_completed", "run_id": run_id, "status": "error"})
        send_note("run_failed", "error", run_id, kwargs)
        if origin_run_id:
            log_event(
                {
                    "event": "reproduce_completed",
                    "run_id": run_id,
                    "origin_run_id": origin_run_id,
                    "status": "error",
                }
            )
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
        r1, r2, r3 = st.columns([1, 1, 1])
        with r1:
            retry = st.button("Retry run", type="primary", width="stretch")
        with r2:
            open_trace = st.button("Open trace", width="stretch")
        with r3:
            resume = st.button("Resume run", width="stretch")
        if retry:
            st.query_params["retry_of"] = err.context.get("run_id") or ""
            st.rerun()
        if open_trace:
            st.query_params["run_id"] = err.context.get("run_id") or ""
            st.query_params["view"] = "trace"
            st.switch_page("pages/02_Results.py")
        if resume:
            st.query_params["resume_from"] = err.context.get("run_id") or ""
            st.rerun()
    except TimeoutError as e:  # pragma: no cover - UI display
        if current_box is not None:
            current_box.update(label="Timeout", state="error")
        err = make_safe_error(e, run_id=run_id, phase=current_phase, step_id=None)
        st.session_state["active_run"]["status"] = "timeout"
        complete_run_meta(run_id, status="timeout")
        timeout_hit(run_id, current_phase)
        log_event({"event": "run_completed", "run_id": run_id, "status": "timeout"})
        send_note("timeout", "timeout", run_id, kwargs)
        if origin_run_id:
            log_event(
                {
                    "event": "reproduce_completed",
                    "run_id": run_id,
                    "origin_run_id": origin_run_id,
                    "status": "timeout",
                }
            )
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
        r1, r2, r3 = st.columns([1, 1, 1])
        with r1:
            retry = st.button("Retry run", type="primary", width="stretch")
        with r2:
            open_trace = st.button("Open trace", width="stretch")
        with r3:
            resume = st.button("Resume run", width="stretch")
        if retry:
            st.query_params["retry_of"] = err.context.get("run_id") or ""
            st.rerun()
        if open_trace:
            st.query_params["run_id"] = err.context.get("run_id") or ""
            st.query_params["view"] = "trace"
            st.switch_page("pages/02_Results.py")
        if resume:
            st.query_params["resume_from"] = err.context.get("run_id") or ""
            st.rerun()
    except Exception as e:  # pragma: no cover - UI display
        if current_box is not None:
            current_box.update(label="Error", state="error")
        err = make_safe_error(e, run_id=run_id, phase=current_phase, step_id=None)
        st.session_state["active_run"]["status"] = "error"
        complete_run_meta(run_id, status="error")
        log_event({"event": "run_completed", "run_id": run_id, "status": "error"})
        send_note("run_failed", "error", run_id, kwargs, {"error": e.__class__.__name__})
        if origin_run_id:
            log_event(
                {
                    "event": "reproduce_completed",
                    "run_id": run_id,
                    "origin_run_id": origin_run_id,
                    "status": "error",
                }
            )
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
            retry = st.button("Retry run", type="primary", width="stretch")
        with r2:
            open_trace = st.button("Open trace", width="stretch")
        if retry:
            st.query_params["retry_of"] = err.context.get("run_id") or ""
            st.rerun()
        if open_trace:
            st.query_params["run_id"] = err.context.get("run_id") or ""
            st.query_params["view"] = "trace"
            st.switch_page("pages/02_Results.py")

    finally:
        session_guard.release(run_id)
        run_lock_released(run_id)
        st.session_state["active_run"] = None
        st.session_state["submit_token"] = None
        run_cancelled(run_id)
        try:
            api_logger.close()
        finally:
            api_loggers.set_api_call_logger(None)


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
