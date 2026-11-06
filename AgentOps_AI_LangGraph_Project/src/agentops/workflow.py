"""Reference orchestrator. Install langgraph extra for explicit graph version."""
from __future__ import annotations

from uuid import uuid4
from .agents import (
    monitoring_agent, investigation_agent, knowledge_agent,
    root_cause_agent, remediation_agent, reporting_agent,
)
from .llm import LLMClient
from .models import IncidentRequest, InvestigationReport


def investigate(request: IncidentRequest, llm: LLMClient | None = None) -> InvestigationReport:
    """Strict sequence: observe -> investigate -> diagnose -> propose -> review.

    There is deliberately NO execution node. A review status is not an
    authorization credential, and it must not automatically trigger a write.
    """
    llm = llm or LLMClient()
    severity = monitoring_agent(request.description)
    evidence, called, failure = investigation_agent(request.pipeline_id, llm)
    _runbooks = knowledge_agent(evidence)
    diagnosis = root_cause_agent(request.pipeline_id, evidence, llm, failure)
    proposal = remediation_agent(diagnosis)
    message = reporting_agent(called, diagnosis, proposal)
    return InvestigationReport(
        id=str(uuid4()), pipeline_id=request.pipeline_id,
        description=request.description, severity=severity, status="pending_review",
        evidence=evidence, diagnosis=diagnosis, proposal=proposal,
        tool_calls=called, mode="llm" if llm.enabled else "synthetic_demo",
        message=message
    )
