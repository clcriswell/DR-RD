"""Starter server mounting bridge routes."""
from fastapi import FastAPI
from .slack_bridge import router as slack_router
from .teams_bridge import router as teams_router
from .jira_bridge import router as jira_router


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(slack_router)
    app.include_router(teams_router)
    app.include_router(jira_router)
    return app

app = create_app()
