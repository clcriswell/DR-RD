from pydantic import BaseModel
from typing import Dict, Any, List


class TestResult(BaseModel):
    test_id: str
    passed: bool
    metrics_observed: Dict[str, float]
    metrics_passfail: Dict[str, bool]
    notes: str = ""


class PoCReport(BaseModel):
    project_id: str
    hypothesis: str
    results: List[TestResult]
    summary: str
