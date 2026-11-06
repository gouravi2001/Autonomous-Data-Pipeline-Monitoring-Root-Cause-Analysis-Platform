"""Real LangGraph interrupt/Command resume demonstration.

Run with: python examples/human_review_interrupt.py
This is an in-memory demonstration and does not perform production actions.
"""
from __future__ import annotations

from typing import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class ReviewState(TypedDict):
    incident_id: str
    proposal: str
    review_status: str


def review_node(state: ReviewState) -> dict:
    answer = interrupt({
        "incident_id": state["incident_id"],
        "proposal": state["proposal"],
        "question": "Approve or reject this simulation proposal?",
    })
    # This node runs again from the top when resumed. Side effects MUST be
    # placed after interrupt and require idempotency before real deployment.
    if answer not in ("approve", "reject"):
        return {"review_status": "needs_manual_review"}
    return {"review_status": "approved_in_simulation" if answer == "approve"
            else "rejected_in_simulation"}


def main():
    graph_builder = StateGraph(ReviewState)
    graph_builder.add_node("request_review", review_node)
    graph_builder.add_edge(START, "request_review")
    graph_builder.add_edge("request_review", END)
    graph = graph_builder.compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "sample-incident-1"}}

    paused = graph.invoke({
        "incident_id": "sample-incident-1",
        "proposal": "Review schema mapping change in staging",
        "review_status": "pending_review",
    }, config=config)
    print("Paused:", paused.get("__interrupt__"))
    # A real service only resumes after checking authenticated reviewer RBAC.
    final = graph.invoke(Command(resume="approve"), config=config)
    print("Final status:", final["review_status"])
    print("No production action executed.")


if __name__ == "__main__":
    main()
