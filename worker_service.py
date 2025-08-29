"""Minimal FastAPI service exposing core.runner.execute_task."""
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

class RunRequest(BaseModel):
    role: str
    title: str
    desc: str = ""
    inputs: dict = Field(default_factory=dict)

@app.post("/run")
async def run(req: RunRequest):
    from core.runner import execute_task
    return execute_task(req.role, req.title, req.desc, req.inputs)

@app.get("/healthz")
async def health():
    return {"status": "ok"}
