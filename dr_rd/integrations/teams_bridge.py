"""Teams bridge shim."""
import os
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()


def _allowed(cmd: str) -> bool:
    allowed = os.environ.get("TEAMS_ALLOWED_COMMANDS", "run").split(",")
    return cmd in allowed


@router.post("/teams/messages")
async def teams_messages(request: Request):
    data = await request.json()
    text = data.get("text", "")
    parts = text.split()
    if len(parts) < 3:
        raise HTTPException(status_code=400, detail="invalid command")
    cmd = parts[0]
    if not _allowed(cmd):
        raise HTTPException(status_code=403, detail="command not allowed")
    role = parts[1]
    title = " ".join(parts[2:]).strip('"')
    from core.runner import execute_task
    result = execute_task(role, title, "", {})
    return {"result": result}
