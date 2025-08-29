from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Org:
    """An organization that owns one or more workspaces."""

    org_id: str
    name: str
    meta: Dict[str, object] = field(default_factory=dict)


@dataclass
class Workspace:
    """A workspace within an organization."""

    org_id: str
    workspace_id: str
    name: str
    meta: Dict[str, object] = field(default_factory=dict)


@dataclass
class Principal:
    """Authenticated entity (user or API key)."""

    principal_id: str
    kind: str  # 'user' | 'api_key'
    org_id: str
    workspace_id: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    disabled: bool = False
    meta: Dict[str, object] = field(default_factory=dict)


@dataclass
class TenantContext:
    """Context object propagated through requests and runs."""

    org_id: str
    workspace_id: Optional[str] = None
    principal: Optional[Principal] = None
    run_id: str = ""
