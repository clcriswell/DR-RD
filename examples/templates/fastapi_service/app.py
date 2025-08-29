from fastapi import FastAPI
from pydantic import BaseModel
from core.runner import execute_task

app = FastAPI()


class Task(BaseModel):
    role: str
    title: str
    desc: str
    inputs: dict


@app.post("/run")
async def run(task: Task):
    return execute_task(task.role, task.title, task.desc, task.inputs)
