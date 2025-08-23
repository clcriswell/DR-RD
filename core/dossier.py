from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from utils.config import load_config
from utils.redaction import load_policy, redact_text


@dataclass
class Evidence:
    source_id: str
    uri: str
    snippet: str


@dataclass
class Finding:
    id: str
    title: str
    body: str
    evidences: List[Evidence] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


class Dossier:
    def __init__(self, policy: Dict[str, Any] | None = None):
        if policy is None:
            cfg = load_config()
            if cfg.get("redaction", {}).get("enabled", True):
                policy_file = cfg.get("redaction", {}).get(
                    "policy_file", "config/redaction.yaml"
                )
                policy = load_policy(policy_file)
            else:
                policy = {}
        self.policy = policy or {}
        self.findings: List[Finding] = []

    def record_finding(self, f: Finding) -> None:
        self.findings.append(f)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "run": {"saved_at": datetime.utcnow().isoformat() + "Z"},
            "findings": [asdict(f) for f in self.findings],
        }

    def save(self, path: Path) -> None:
        data = self.to_dict()
        if self.policy:
            for f in data["findings"]:
                f["title"] = redact_text(f.get("title", ""), policy=self.policy)
                f["body"] = redact_text(f.get("body", ""), policy=self.policy)
                for e in f.get("evidences", []):
                    e["snippet"] = redact_text(e.get("snippet", ""), policy=self.policy)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
