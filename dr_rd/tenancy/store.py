from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List, Optional

from .models import Org, Workspace, Principal

BASE_DIR = Path.home() / ".dr_rd" / "tenants"
BASE_DIR.mkdir(parents=True, exist_ok=True)


def _path(name: str) -> Path:
    return BASE_DIR / f"{name}.jsonl"


def _read_all(path: Path) -> List[dict]:
    if not path.exists():
        return []
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def _append(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(obj) + "\n")


# ---- Org operations -------------------------------------------------------

def create_org(name: str, meta: Optional[dict] = None) -> Org:
    org = Org(org_id=uuid.uuid4().hex, name=name, meta=meta or {})
    _append(_path("orgs"), asdict(org))
    return org


def list_orgs() -> List[Org]:
    return [Org(**rec) for rec in _read_all(_path("orgs"))]


def get_org(org_id: str) -> Optional[Org]:
    for org in list_orgs():
        if org.org_id == org_id:
            return org
    return None


# ---- Workspace operations -------------------------------------------------

def create_workspace(org_id: str, name: str, meta: Optional[dict] = None) -> Workspace:
    ws = Workspace(org_id=org_id, workspace_id=uuid.uuid4().hex, name=name, meta=meta or {})
    _append(_path("workspaces"), asdict(ws))
    return ws


def list_workspaces(org_id: Optional[str] = None) -> List[Workspace]:
    wss = [Workspace(**rec) for rec in _read_all(_path("workspaces"))]
    if org_id:
        wss = [w for w in wss if w.org_id == org_id]
    return wss


def get_workspace(org_id: str, workspace_id: str) -> Optional[Workspace]:
    for ws in list_workspaces(org_id):
        if ws.workspace_id == workspace_id:
            return ws
    return None


# ---- Principal operations -------------------------------------------------

def create_principal(
    principal_id: str,
    kind: str,
    org_id: str,
    workspace_id: Optional[str] = None,
    roles: Optional[Iterable[str]] = None,
    disabled: bool = False,
    meta: Optional[dict] = None,
) -> Principal:
    principal = Principal(
        principal_id=principal_id,
        kind=kind,
        org_id=org_id,
        workspace_id=workspace_id,
        roles=list(roles or []),
        disabled=disabled,
        meta=meta or {},
    )
    _append(_path("principals"), asdict(principal))
    return principal


def list_principals(org_id: Optional[str] = None, workspace_id: Optional[str] = None) -> List[Principal]:
    principals = [Principal(**rec) for rec in _read_all(_path("principals"))]
    if org_id:
        principals = [p for p in principals if p.org_id == org_id]
    if workspace_id:
        principals = [p for p in principals if p.workspace_id == workspace_id]
    return principals


def get_principal(principal_id: str) -> Optional[Principal]:
    for p in list_principals():
        if p.principal_id == principal_id:
            return p
    return None
