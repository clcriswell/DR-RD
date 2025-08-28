from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class KBSource:
    """Source metadata for knowledge base records."""

    id: str
    kind: str  # "web" | "tool" | "file"
    url: Optional[str] = None
    title: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KBRecord:
    """Stored artifact produced by an agent run."""

    id: str
    run_id: str
    agent_role: str
    task_title: str
    task_desc: str
    inputs: Dict[str, Any]
    output_json: Dict[str, Any]
    sources: List[KBSource] = field(default_factory=list)
    ts: float = 0.0
    tags: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    provenance_span_ids: List[str] = field(default_factory=list)

    def asdict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["sources"] = [asdict(s) for s in self.sources]
        return d
