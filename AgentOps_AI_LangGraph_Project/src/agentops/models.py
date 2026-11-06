from __future__ import annotations

from enum import Enum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class IncidentRequest(StrictModel):
    pipeline_id: Literal["daily_revenue_etl", "customer_orders_hourly"]
    description: str = Field(min_length=5, max_length=400)


class Evidence(StrictModel):
    id: str
    source: str
    data: dict


class Diagnosis(StrictModel):
    category: Literal["schema_drift", "freshness", "unknown"]
    root_cause: str = Field(min_length=5, max_length=700)
    evidence_ids: list[str] = Field(max_length=10)
    confidence: float = Field(ge=0, le=1)


class Proposal(StrictModel):
    action: Literal["review_schema_mapping", "inspect_upstream_source", "manual_investigation"]
    explanation: str
    requires_human_approval: bool = True


class ReviewRequest(StrictModel):
    reviewer: str = Field(min_length=3, max_length=100)
    decision: Literal["approve", "reject"]
    comment: str = Field(default="", max_length=500)


class InvestigationReport(StrictModel):
    id: str
    pipeline_id: str
    description: str
    severity: Literal["low", "medium", "high"]
    status: Literal["pending_review", "approved_in_simulation", "rejected_in_simulation"]
    evidence: list[Evidence]
    diagnosis: Diagnosis
    proposal: Proposal
    tool_calls: list[str]
    mode: Literal["synthetic_demo", "llm"]
    message: str


class ToolName(str, Enum):
    STATUS = "get_pipeline_status"
    LOGS = "get_recent_logs"
    SCHEMA = "get_schema_diff"
    RUNBOOK = "get_runbook"
