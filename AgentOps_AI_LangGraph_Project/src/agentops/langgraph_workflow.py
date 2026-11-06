"""LangGraph implementation of the incident investigation workflow.

Install: pip install -e '.[langgraph]'
Activate API workflow: AGENTOPS_ENGINE=langgraph uvicorn agentops.main:app --reload

This graph performs read-only investigation and generates proposals ONLY.
Recording a review in the API does not execute any production remediation.
"""
from __future__ import annotations

from typing import Any, Literal, TypedDict
from uuid import uuid4

from .agents import (
    monitoring_agent, investigation_agent, knowledge_agent,
    root_cause_agent, remediation_agent, reporting_agent,
)
from .llm import LLMClient
from .models import Diagnosis, Evidence, IncidentRequest, InvestigationReport, Proposal


class IncidentState(TypedDict, total=False):
    request: IncidentRequest
    severity: str
    evidence: list[Evidence]
    calls: list[str]
    tool_failed: bool
    runbook_count: int
    knowledge_matches: list[dict[str, str]]
    diagnosis: Diagnosis
    proposal: Proposal
    policy_passed: bool
    message: str


def build_graph(llm: LLMClient | None = None):
    """Build the actual LangGraph StateGraph with a conditional policy branch."""
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise RuntimeError("Install the optional extra: pip install -e '.[langgraph]'") from exc

    llm = llm if llm is not None else LLMClient()

    def monitor(state: IncidentState) -> dict[str, Any]:
        return {"severity": monitoring_agent(state["request"].description)}

    def investigate_node(state: IncidentState) -> dict[str, Any]:
        evidence, calls, failed = investigation_agent(state["request"].pipeline_id, llm)
        return {"evidence": evidence, "calls": calls, "tool_failed": failed}

    def retrieve_knowledge(state: IncidentState) -> dict[str, Any]:
        from .langchain_retrieval import retrieve_runbooks
        # LangChain in-memory toy retrieval. Retrieval results are contextual
        # support only; they never authorize a diagnosis or execution by themselves.
        query = state["request"].description + " " + " ".join(
            str(e.data)[:1000] for e in state["evidence"]
        )
        hits = retrieve_runbooks(query, k=2)
        return {"runbook_count": len(knowledge_agent(state["evidence"])),
                "knowledge_matches": hits}

    def diagnose(state: IncidentState) -> dict[str, Any]:
        return {"diagnosis": root_cause_agent(
            state["request"].pipeline_id,
            state["evidence"], llm, state["tool_failed"]
        )}

    def propose(state: IncidentState) -> dict[str, Any]:
        return {"proposal": remediation_agent(state["diagnosis"])}

    def validate_policy(state: IncidentState) -> dict[str, Any]:
        diagnosis = state["diagnosis"]
        evidence_ids = {e.id for e in state["evidence"]}
        grounded = bool(diagnosis.evidence_ids) and set(diagnosis.evidence_ids).issubset(evidence_ids)
        permitted = state["proposal"].action in {"review_schema_mapping", "inspect_upstream_source"}
        return {"policy_passed": grounded and permitted and not state["tool_failed"]}

    def next_step(state: IncidentState) -> Literal["report", "escalate"]:
        return "report" if state["policy_passed"] else "escalate"

    def escalate(state: IncidentState) -> dict[str, Any]:
        return {"proposal": Proposal(
            action="manual_investigation",
            explanation="Evidence or policy checks were insufficient; manual review is required",
        )}

    def report(state: IncidentState) -> dict[str, Any]:
        return {"message": reporting_agent(state["calls"], state["diagnosis"], state["proposal"])}

    graph = StateGraph(IncidentState)
    for name, fn in (
        ("monitor", monitor),
        ("investigate", investigate_node),
        ("retrieve_knowledge", retrieve_knowledge),
        ("diagnose", diagnose),
        ("propose", propose),
        ("validate_policy", validate_policy),
        ("escalate", escalate),
        ("report", report),
    ):
        graph.add_node(name, fn)

    graph.add_edge(START, "monitor")
    graph.add_edge("monitor", "investigate")
    graph.add_edge("investigate", "retrieve_knowledge")
    graph.add_edge("retrieve_knowledge", "diagnose")
    graph.add_edge("diagnose", "propose")
    graph.add_edge("propose", "validate_policy")
    graph.add_conditional_edges(
        "validate_policy", next_step, {"report": "report", "escalate": "escalate"}
    )
    graph.add_edge("escalate", "report")
    graph.add_edge("report", END)
    return graph.compile()


def run_graph(request: IncidentRequest, llm: LLMClient | None = None) -> InvestigationReport:
    """Run the LangGraph workflow and return a validated incident report."""
    llm = llm if llm is not None else LLMClient()
    state = build_graph(llm).invoke({"request": request})
    return InvestigationReport(
        id=str(uuid4()),
        pipeline_id=request.pipeline_id,
        description=request.description,
        severity=state["severity"],
        status="pending_review",
        evidence=state["evidence"],
        diagnosis=state["diagnosis"],
        proposal=state["proposal"],
        tool_calls=state["calls"],
        mode="llm" if llm.enabled else "synthetic_demo",
        message=state["message"],
    )
