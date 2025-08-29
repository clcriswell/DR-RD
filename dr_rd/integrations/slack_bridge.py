"""Slack bridge shim mapping commands to runner."""
import os
import json
import hmac
import hashlib
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()


def _verify(request: Request, body: bytes) -> None:
    secret = os.environ.get("SLACK_SIGNING_SECRET")
    if not secret:
        raise HTTPException(status_code=400, detail="missing signing secret")
    ts = request.headers.get("X-Slack-Request-Timestamp", "0")
    sig = request.headers.get("X-Slack-Signature", "")
    basestring = f"v0:{ts}:{body.decode()}"
    my_sig = "v0=" + hmac.new(secret.encode(), basestring.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(my_sig, sig):
        raise HTTPException(status_code=403, detail="invalid signature")


@router.post("/slack/events")
async def slack_events(request: Request):
    body = await request.body()
    _verify(request, body)
    payload = json.loads(body)
    text = payload.get("text", "")
    parts = text.split()
    if len(parts) < 3 or parts[0] != "run":
        raise HTTPException(status_code=400, detail="invalid command")
    role = parts[1]
    title = " ".join(parts[2:]).strip('"')
    from core.runner import execute_task
    result = execute_task(role, title, "", {})
    return {"ok": True, "result": result}
