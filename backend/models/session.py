from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
import uuid
from datetime import datetime


class ContextType(str, Enum):
    STARTUP = "startup"
    VENDOR = "vendor"
    PROJECT = "project"
    PRODUCT = "product"
    WORKFLOW = "workflow"
    ENTERPRISE = "enterprise"


class AssessmentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class AssessmentRequest(BaseModel):
    name: str = Field(description="Name of the business, product, vendor, or project")
    description: str = Field(description="Detailed description to assess")
    context_type: ContextType = ContextType.STARTUP
    industry: str = Field(default="technology")
    additional_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional structured metadata: team_size, stage, handles_pii, etc."
    )


class AssessmentSession(BaseModel):
    session_id: str = Field(default_factory=lambda: f"ra-{uuid.uuid4().hex[:10]}")
    request: AssessmentRequest
    status: AssessmentStatus = AssessmentStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    error: str | None = None


class AssessmentResponse(BaseModel):
    session_id: str
    status: AssessmentStatus
    message: str = ""
    report: dict | None = None
