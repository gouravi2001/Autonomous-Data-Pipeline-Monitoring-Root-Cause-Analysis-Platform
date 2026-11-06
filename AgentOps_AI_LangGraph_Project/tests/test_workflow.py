from agentops.models import IncidentRequest
from agentops.workflow import investigate


def test_schema_drift_has_evidence_and_needs_approval(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    r = investigate(IncidentRequest(pipeline_id="daily_revenue_etl", description="Revenue dropped"))
    assert r.diagnosis.category == "schema_drift"
    assert len(r.diagnosis.evidence_ids) == 2
    assert set(r.diagnosis.evidence_ids) <= {x.id for x in r.evidence}
    assert r.proposal.action == "review_schema_mapping"
    assert r.proposal.requires_human_approval is True
    assert r.status == "pending_review"
    assert r.mode == "synthetic_demo"
    assert len(r.tool_calls) <= 4


def test_freshness_does_not_propose_schema_fix(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    r = investigate(IncidentRequest(pipeline_id="customer_orders_hourly", description="Data arrived late"))
    assert r.proposal.action == "inspect_upstream_source"
    assert r.status == "pending_review"
