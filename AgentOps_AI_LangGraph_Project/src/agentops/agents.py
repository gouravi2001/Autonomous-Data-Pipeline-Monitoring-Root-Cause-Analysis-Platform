from __future__ import annotations

from .llm import LLMClient
from .models import Diagnosis, Evidence, Proposal
from .tools import execute_readonly_tool, authorized_tools

MAX_TOOL_CALLS = 4


def monitoring_agent(description: str) -> str:
    """Deterministic gate: no model needed to classify urgency from structured checks."""
    return "high" if "revenue" in description.lower() else "medium"


def investigation_agent(pipeline_id: str, llm: LLMClient) -> tuple[list[Evidence], list[str], bool]:
    """LLM chooses among bounded *read-only* diagnostic tools."""
    evidence: list[Evidence] = []
    called: list[str] = []
    fallback_order = authorized_tools()
    model_failed = False
    for _ in range(MAX_TOOL_CALLS):
        if llm.enabled:
            try:
                choice = llm.pick_tool(pipeline_id, [e.model_dump() for e in evidence], called)
                name = choice.next_tool
            except Exception:
                model_failed = True
                break  # Fail closed; do not silently switch to false 'AI' reasoning.
        else:
            name = next((x for x in fallback_order if x not in called), "done")
        if name == "done":
            break
        if name not in authorized_tools() or name in called:
            model_failed = True
            break
        data = execute_readonly_tool(name, pipeline_id)
        called.append(name)
        evidence.append(Evidence(id=f"E{len(evidence)+1}", source=name, data=data))
    return evidence, called, model_failed


def knowledge_agent(evidence: list[Evidence]) -> list[Evidence]:
    """Select already-fetched authoritative runbooks; not untrusted web searches."""
    return [ev for ev in evidence if ev.source == "get_runbook"]


def root_cause_agent(pipeline_id: str, evidence: list[Evidence], llm: LLMClient,
                     tool_failure: bool) -> Diagnosis:
    if tool_failure:
        return Diagnosis(category="unknown", root_cause="Diagnostic tool planning failed; human investigation required",
                         evidence_ids=[], confidence=0)
    evidence_by_tool = {e.source: e for e in evidence}
    if llm.enabled:
        try:
            diag = llm.diagnose(pipeline_id, [e.model_dump() for e in evidence])
            known = {e.id for e in evidence}
            if not diag.evidence_ids or not set(diag.evidence_ids).issubset(known):
                raise ValueError("Ungrounded diagnosis")
            if diag.confidence > 0.85 and len(diag.evidence_ids) < 2:
                raise ValueError("Single evidence does not support high confidence")
            return diag
        except Exception:
            return Diagnosis(category="unknown", root_cause="Model reasoning was invalid or unavailable; escalate",
                             evidence_ids=[], confidence=0)
    # Transparent, deterministic synthetic demo: no claims of model reasoning.
    diff = evidence_by_tool.get("get_schema_diff")
    logs = evidence_by_tool.get("get_recent_logs")
    if (diff and logs and diff.data.get("removed_columns") == ["order_amount"]
            and diff.data.get("added_columns") == ["total_amount"]):
        return Diagnosis(category="schema_drift",
                         root_cause="The upstream schema replaced order_amount with total_amount, causing transform_revenue to fail",
                         evidence_ids=[diff.id, logs.id], confidence=0.92)
    status = evidence_by_tool.get("get_pipeline_status")
    if status and status.data.get("last_run") == "delayed":
        return Diagnosis(category="freshness", root_cause="Upstream data delivery is delayed",
                         evidence_ids=[status.id], confidence=0.70)
    return Diagnosis(category="unknown", root_cause="Insufficient evidence; escalate",
                     evidence_ids=[], confidence=0)


def remediation_agent(diagnosis: Diagnosis) -> Proposal:
    """Policy maps diagnoses to proposals; no model gets write capability."""
    if diagnosis.category == "schema_drift" and diagnosis.confidence >= 0.85 and len(diagnosis.evidence_ids) >= 2:
        return Proposal(action="review_schema_mapping", explanation="Review schema mapping in staging, test, and request an authorized rerun")
    if diagnosis.category == "freshness" and diagnosis.confidence >= 0.65:
        return Proposal(action="inspect_upstream_source", explanation="Check delivery lag and upstream SLA")
    return Proposal(action="manual_investigation", explanation="Escalate for human diagnosis")


def reporting_agent(tool_calls: list[str], diagnosis: Diagnosis, proposal: Proposal) -> str:
    return (f"Investigation used {len(tool_calls)} read-only tools. "
            f"Proposed cause: {diagnosis.category} ({diagnosis.confidence:.0%} confidence). "
            f"Suggested action: {proposal.action}. Human approval is required; no change was executed.")
