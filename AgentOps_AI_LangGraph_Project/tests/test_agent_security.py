from types import SimpleNamespace
from agentops.agents import investigation_agent, root_cause_agent, remediation_agent
from agentops.models import Diagnosis, Evidence


class RogueLLM:
    enabled = True
    def pick_tool(self, pipeline_id, evidence, called):
        return SimpleNamespace(next_tool="delete_tables")


def test_model_cannot_invoke_unlisted_tool():
    evidence, called, failed = investigation_agent("daily_revenue_etl", RogueLLM())
    assert failed is True
    assert evidence == [] and called == []
    d = root_cause_agent("daily_revenue_etl", evidence, RogueLLM(), failed)
    assert d.category == "unknown"
    assert remediation_agent(d).action == "manual_investigation"


class HallucinationLLM:
    enabled = True
    def diagnose(self, pipeline_id, evidence):
        return Diagnosis(category="schema_drift", root_cause="Looks like schema drift",
                         evidence_ids=["NONEXISTENT"], confidence=0.99)


def test_model_cannot_cite_nonexistent_evidence():
    e = Evidence(id="E1", source="get_schema_diff", data={"removed_columns": []})
    d = root_cause_agent("daily_revenue_etl", [e], HallucinationLLM(), False)
    assert d.category == "unknown"
    assert d.confidence == 0
