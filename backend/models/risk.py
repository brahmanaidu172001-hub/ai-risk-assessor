from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
import uuid
from datetime import datetime


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskCategory(str, Enum):
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    CYBER = "cyber"
    MARKET = "market"
    PRODUCT = "product"
    VENDOR = "vendor"
    EXECUTION = "execution"


class RiskFinding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    category: RiskCategory
    title: str
    description: str
    severity: RiskLevel
    likelihood: int = Field(ge=1, le=5, description="1=rare, 5=almost certain")
    impact: int = Field(ge=1, le=5, description="1=negligible, 5=catastrophic")
    score: float = Field(ge=0, le=100)
    evidence: list[str] = Field(default_factory=list)
    mitigations: list[str] = Field(default_factory=list)


class CategoryReport(BaseModel):
    category: RiskCategory
    score: float = Field(ge=0, le=100)
    level: RiskLevel
    findings: list[RiskFinding] = Field(default_factory=list)
    summary: str = ""


class ActionItem(BaseModel):
    priority: int
    title: str
    description: str
    owner: str = "Risk Owner"
    timeframe: str  # e.g. "Immediate", "30 days", "90 days"
    category: RiskCategory


class RiskReport(BaseModel):
    session_id: str
    entity_name: str
    context_type: str
    industry: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    overall_score: float = Field(ge=0, le=100)
    overall_level: RiskLevel
    risk_summary: str

    category_reports: list[CategoryReport] = Field(default_factory=list)
    top_risks: list[RiskFinding] = Field(default_factory=list)
    action_plan: list[ActionItem] = Field(default_factory=list)
    executive_summary: str = ""

    agent_outputs: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")
