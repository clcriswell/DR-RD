from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import uuid


class EvidenceItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    role: str
    task_title: str
    claim: str
    sources: List[str] = []
    quotes: List[str] = []
    confidence: float = 0.0   # 0..1
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class EvidenceSet(BaseModel):
    project_id: str
    items: List[EvidenceItem] = []

    def add(self, **kwargs) -> None:
        self.items.append(EvidenceItem(project_id=self.project_id, **kwargs))

    def as_dicts(self) -> List[Dict]:
        return [i.model_dump() for i in self.items]
