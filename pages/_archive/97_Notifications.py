import streamlit as st

from utils.prefs import load_prefs, save_prefs
from utils.notify import Note, dispatch as notify_dispatch
from utils.telemetry import notifications_saved, notification_test_sent
from utils.secrets import get as get_secret

st.set_page_config(page_title="Notifications")

st.title("Notifications")

prefs = load_prefs()
np = prefs.get("notifications", {})

enabled = st.checkbox("Enabled", value=np.get("enabled", True))
channels = st.multiselect("Channels", ["slack", "email", "webhook"], default=np.get("channels", []))
slack_mention = st.text_input("Slack mention", np.get("slack_mention", ""))
email_to_str = ", ".join(np.get("email_to", []))
email_to_input = st.text_input("Email recipients", email_to_str)

slack_hint = "✅ Slack webhook configured" if get_secret("SLACK_WEBHOOK_URL") else "⚠️ Slack webhook not set"
st.caption(slack_hint)
smtp_ok = all(get_secret(k) for k in ["SMTP_HOST", "SMTP_FROM"])
st.caption("✅ SMTP configured" if smtp_ok else "⚠️ SMTP incomplete")
webhook_hint = "✅ Webhook URL set" if get_secret("WEBHOOK_URL") else "⚠️ Webhook URL missing"
st.caption(webhook_hint)

events = {}
for ev in [
    "run_completed",
    "run_failed",
    "run_cancelled",
    "timeout",
    "budget_exceeded",
    "safety_blocked",
]:
    label = ev.replace("_", " ").title()
    events[ev] = st.checkbox(label, value=np.get("events", {}).get(ev, True))

if st.button("Save"):
    updated = prefs.copy()
    updated["notifications"] = {
        "enabled": bool(enabled),
        "channels": channels,
        "email_to": [e.strip() for e in email_to_input.split(",") if e.strip()][:10],
        "slack_mention": slack_mention,
        "events": events,
    }
    save_prefs(updated)
    notifications_saved(channels, sum(events.values()))
    st.success("Saved")

for ch in ["slack", "email", "webhook"]:
    if st.button(f"Send test {ch}"):
        note = Note(event="test", run_id="test", status="success", mode="test", idea_preview="test")
        tmp_prefs = {
            "notifications": {
                "enabled": True,
                "channels": [ch],
                "email_to": [e.strip() for e in email_to_input.split(",") if e.strip()][:10],
                "slack_mention": slack_mention,
                "events": {"test": True},
            }
        }
        ok = bool(notify_dispatch(note, tmp_prefs).get(ch))
        notification_test_sent(ch, ok)
        st.toast(f"{ch} {'sent' if ok else 'failed'}")
