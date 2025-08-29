"""Jira bridge shim."""
import os
import requests
from fastapi import APIRouter, Request

router = APIRouter()


def _issue_payload(summary: str, description: str) -> dict:
    project = os.environ.get("JIRA_PROJECT_KEY", "")
    return {
        "fields": {
            "project": {"key": project},
            "summary": summary,
            "description": description,
            "issuetype": {"name": "Task"},
        }
    }


@router.post("/jira/hook")
async def jira_hook(request: Request):
    data = await request.json()
    summary = data.get("summary", "")
    description = data.get("description", "")
    payload = _issue_payload(summary, description)
    base = os.environ.get("JIRA_BASE_URL")
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN")
    resp = requests.post(f"{base}/rest/api/3/issue", json=payload, auth=(email, token))
    resp.raise_for_status()
    return resp.json()
