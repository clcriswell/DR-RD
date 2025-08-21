from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class Requirement(BaseModel):
    id: str
    text: str
    priority: str = "M"  # M/S/C

class Interface(BaseModel):
    name: str
    producer: str
    consumer: str
    contract: str

class DataFlow(BaseModel):
    source: str
    sink: str
    data: str
    frequency: str = ""

class SecurityReq(BaseModel):
    id: str
    control: str
    rationale: str = ""

class RiskItem(BaseModel):
    id: str
    text: str
    severity: str = "H"
    mitigation: str = ""

class Milestone(BaseModel):
    id: str
    name: str
    due: str = ""
    deliverables: List[str] = []

class WorkItem(BaseModel):
    id: str
    title: str
    owner: str = "TBD"
    deps: List[str] = []

class BOMItem(BaseModel):
    part_no: str
    desc: str
    qty: int = 1
    unit_cost: float = 0.0
    vendor: str = "TBD"

class BudgetPhase(BaseModel):
    phase: str
    cost_usd: float = 0.0

class SDD(BaseModel):
    title: str
    overview: str
    requirements: List[Requirement] = []
    architecture: str
    interfaces: List[Interface] = []
    data_flows: List[DataFlow] = []
    security: List[SecurityReq] = []
    risks: List[RiskItem] = []

class ImplPlan(BaseModel):
    work: List[WorkItem] = []
    milestones: List[Milestone] = []
    rollback: str = ""
    bom: List[BOMItem] = []
    budget: List[BudgetPhase] = []
