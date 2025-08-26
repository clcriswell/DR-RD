from __future__ import annotations

from enum import Enum
from typing import Dict, List, Any
from pydantic import BaseModel


class ComplianceChecklistItem(BaseModel):
    id: str
    text: str
    required: bool = True
    jurisdiction: str = ""
    tag: str = ""


class ComplianceProfile(BaseModel):
    id: str
    name: str
    items: List[ComplianceChecklistItem]


class CitationKind(str, Enum):
    statute = "statute"
    rule = "rule"
    patent = "patent"
    standard = "standard"
    other = "other"


class Citation(BaseModel):
    id: str
    claim_id: str
    source_id: str
    url: str
    domain: str
    kind: CitationKind


class ComplianceReport(BaseModel):
    coverage: float
    unmet: List[str]
    citations: List[Citation]
    notes: Dict[str, Any]
