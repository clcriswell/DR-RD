from fastapi import FastAPI
from pydantic import BaseModel
from core.runner import execute_task

app = FastAPI()


class Task(BaseModel):
    role: str
    title: str
    desc: str
    inputs: dict | list[str] | None = None


def _coerce_inputs(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return {"items": list(value)}
    if value is None:
        return {}
    return {"value": value}


@app.post("/run")
async def run(task: Task):
    return execute_task(task.role, task.title, task.desc, _coerce_inputs(task.inputs))
