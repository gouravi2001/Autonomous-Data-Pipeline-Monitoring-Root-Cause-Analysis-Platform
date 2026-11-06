"""Runs only if the optional LangGraph package is installed."""
import pytest

langgraph = pytest.importorskip("langgraph")
from agentops.langgraph_workflow import run_graph
from agentops.models import IncidentRequest


def test_real_langgraph_graph_runs(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    request = IncidentRequest(
        pipeline_id="daily_revenue_etl",
        description="Revenue pipeline failed due to schema drift",
    )
    report = run_graph(request)
    assert report.diagnosis.category == "schema_drift"
    assert report.proposal.action == "review_schema_mapping"
    assert report.status == "pending_review"
    assert report.proposal.requires_human_approval
    assert len(report.tool_calls) <= 4


def test_real_langgraph_unknown_evidence_escalates(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    request = IncidentRequest(
        pipeline_id="customer_orders_hourly",
        description="Hourly customer orders arrived late",
    )
    report = run_graph(request)
    assert report.diagnosis.category == "freshness"
    assert report.proposal.action == "inspect_upstream_source"
