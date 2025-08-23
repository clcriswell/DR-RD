import json
import re
import uuid
from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel, Field, field_validator


class EvidenceItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    role: str
    task_title: str = ""
    claim: str = ""
    evidence: str = ""
    sources: List[str] = Field(default_factory=list)
    quotes: List[str] = Field(default_factory=list)
    confidence: float = 0.0  # 0..1
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    meta: dict | None = None

    @field_validator("claim", "evidence", mode="before")
    @classmethod
    def _coerce_text(cls, v):
        if v is None:
            return ""
        if isinstance(v, (dict, list)):
            return json.dumps(v, ensure_ascii=False, separators=(",", ":"))
        return str(v)

    @field_validator("sources", mode="before")
    @classmethod
    def _coerce_sources(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [s.strip() for s in re.split(r"[\n,]+", v) if s.strip()]
        if isinstance(v, dict):
            urls = v.get("urls") or v.get("links")
            if isinstance(urls, list):
                return [str(u) for u in urls]
            return [json.dumps(v, ensure_ascii=False, separators=(",", ":"))]
        if isinstance(v, list):
            out: List[str] = []
            for item in v:
                if isinstance(item, (dict, list)):
                    out.append(json.dumps(item, ensure_ascii=False, separators=(",", ":")))
                else:
                    out.append(str(item))
            return out
        return [str(v)]

    @field_validator("cost_usd", mode="before")
    @classmethod
    def _coerce_cost(cls, v):
        if v is None:
            return 0.0
        try:
            return float(v)
        except Exception:
            return 0.0


class EvidenceSet(BaseModel):
    project_id: str
    items: List[EvidenceItem] = Field(default_factory=list)

    def add(self, **kwargs) -> None:
        claim = kwargs.get("claim")
        if claim is not None and not isinstance(claim, str):
            try:
                kwargs["claim"] = json.dumps(claim, ensure_ascii=False)
            except Exception:
                kwargs["claim"] = str(claim)
        self.items.append(EvidenceItem(project_id=self.project_id, **kwargs))

    def as_dicts(self) -> List[Dict]:
        return [i.model_dump() for i in self.items]
