import pytest
from agentops.models import Diagnosis
from agentops.tools import ToolDenied, execute_readonly_tool
from agentops.agents import remediation_agent


@pytest.mark.parametrize("name", ["run_sql", "exec_shell", "fetch_url", "delete_tables", "DROP TABLE incidents"])
def test_unlisted_tools_are_never_callable(name):
    with pytest.raises(ToolDenied):
        execute_readonly_tool(name, "daily_revenue_etl")


def test_unknown_tenant_pipeline_is_denied():
    with pytest.raises(ToolDenied):
        execute_readonly_tool("get_recent_logs", "other_company_warehouse")


def test_low_confidence_schema_cannot_be_proposed_as_safe_mapping():
    d = Diagnosis(category="schema_drift", root_cause="Possibly a schema changed", evidence_ids=["E1"], confidence=0.4)
    assert remediation_agent(d).action == "manual_investigation"


def test_diagnosis_confidence_is_validated():
    with pytest.raises(ValueError):
        Diagnosis(category="schema_drift", root_cause="A schema change may have occurred", evidence_ids=[], confidence=9)
