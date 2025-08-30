from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List
import hmac
import hashlib
import json
import smtplib
import ssl
import time
import textwrap
import urllib.request
from email.message import EmailMessage

from .secrets import get as get_secret
from .redaction import redact_text
from .pricing import get as price_get  # optional for cost formatting


@dataclass(frozen=True)
class Note:
    event: str            # e.g., "run_completed"
    run_id: str
    status: str           # "success"|"error"|"cancelled"|"timeout"
    mode: str
    idea_preview: str
    totals: Dict[str, Any] | None = None   # {tokens, cost_usd, duration_s}
    url: str | None = None                 # deep link if available
    extra: Dict[str, Any] | None = None    # errors, safety categories


def _format_plain(note: Note) -> str:
    t = note.totals or {}
    cost = f"${t.get('cost_usd', 0):.2f}" if 'cost_usd' in t else "n/a"
    dur = f"{int(t.get('duration_s', 0))}s"
    preview = redact_text((note.idea_preview or "")[:160])
    return textwrap.dedent(
        f"""
        DR RD — {note.event.replace('_',' ').title()}
        Run: {note.run_id}  Status: {note.status}  Mode: {note.mode}
        Totals: tokens={t.get('tokens','n/a')}  cost={cost}  duration={dur}
        Idea: {preview}
        Link: {note.url or 'n/a'}
        """
    ).strip()


def _slack_send(note: Note, mention: str = "") -> bool:
    url = get_secret("SLACK_WEBHOOK_URL")
    if not url:
        return False
    cost = (
        f"${note.totals.get('cost_usd'):.2f}"
        if note.totals and 'cost_usd' in note.totals
        else "n/a"
    )
    blocks: List[Dict[str, Any]] = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*DR RD — {note.event.replace('_',' ').title()}*"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Run ID:*\n`{note.run_id}`"},
                {"type": "mrkdwn", "text": f"*Status:*\n{note.status}"},
                {"type": "mrkdwn", "text": f"*Mode:*\n{note.mode}"},
                {"type": "mrkdwn", "text": f"*Cost:*\n{cost}"},
            ],
        },
    ]
    if note.url:
        blocks.append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Open Trace"},
                        "url": note.url,
                    }
                ],
            }
        )
    if mention:
        blocks.insert(0, {"type": "section", "text": {"type": "mrkdwn", "text": mention}})
    body = json.dumps({"blocks": blocks}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5):
        return True


def _email_send(note: Note, to_list: List[str]) -> bool:
    host = get_secret("SMTP_HOST")
    port = int(get_secret("SMTP_PORT") or 587)
    user = get_secret("SMTP_USER")
    pwd = get_secret("SMTP_PASS")
    sender = get_secret("SMTP_FROM")
    if not (host and port and sender and to_list):
        return False
    msg = EmailMessage()
    msg["Subject"] = f"[DR RD] {note.event.replace('_',' ').title()} — {note.run_id}"
    msg["From"] = sender
    msg["To"] = ", ".join(to_list)
    msg.set_content(_format_plain(note))
    ctx = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=8) as s:
        if (get_secret("SMTP_TLS") or "1") != "0":
            s.starttls(context=ctx)
        if user and pwd:
            s.login(user, pwd)
        s.send_message(msg)
    return True


def _webhook_send(note: Note) -> bool:
    url = get_secret("WEBHOOK_URL")
    if not url:
        return False
    payload = {
        "ts": time.time(),
        "event": note.event,
        "run_id": note.run_id,
        "status": note.status,
        "mode": note.mode,
        "totals": note.totals,
        "url": note.url,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    secret = get_secret("WEBHOOK_SECRET")
    if secret:
        sig = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        headers["X-DRRD-Signature"] = sig
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=5):
        return True


def dispatch(note: Note, prefs: Dict[str, Any]) -> Dict[str, bool]:
    np = prefs.get("notifications", {})
    if not np.get("enabled"):
        return {"enabled": False}
    if note.event != "test" and not np.get("events", {}).get(note.event, False):
        return {"enabled": False}
    chans = set(np.get("channels", []))
    results: Dict[str, bool] = {}
    try:
        if "slack" in chans:
            results["slack"] = _slack_send(note, np.get("slack_mention", ""))
    except Exception:
        results["slack"] = False
    try:
        if "email" in chans:
            to_list = np.get("email_to") or []
            results["email"] = _email_send(note, to_list)
    except Exception:
        results["email"] = False
    try:
        if "webhook" in chans:
            results["webhook"] = _webhook_send(note)
    except Exception:
        results["webhook"] = False
    return results


__all__ = ["Note", "dispatch"]
