from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any


class Metric(BaseModel):
    name: str
    target: float
    operator: str = Field(pattern="^(>=|<=|==|>|<)$")
    unit: Optional[str] = None


class TestCase(BaseModel):
    id: str
    title: str
    inputs: Dict[str, Any] = {}
    metrics: List[Metric] = []
    safety_notes: Optional[str] = None


class TestPlan(BaseModel):
    project_id: str
    hypothesis: str
    tests: List[TestCase] = []
    stop_on_fail: bool = True
