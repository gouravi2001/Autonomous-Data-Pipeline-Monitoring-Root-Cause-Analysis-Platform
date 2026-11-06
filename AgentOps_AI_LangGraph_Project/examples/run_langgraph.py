"""Run the six-agent LangGraph workflow directly (no API or database)."""
from agentops.langgraph_workflow import run_graph
from agentops.models import IncidentRequest

request = IncidentRequest(
    pipeline_id="daily_revenue_etl",
    description="The revenue pipeline failed after an upstream schema update",
)
report = run_graph(request)
print(report.model_dump_json(indent=2))
