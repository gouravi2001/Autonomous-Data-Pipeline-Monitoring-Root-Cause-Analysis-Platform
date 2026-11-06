from agentops.models import IncidentRequest
from agentops.workflow import investigate

report = investigate(IncidentRequest(
    pipeline_id="daily_revenue_etl",
    description="Daily revenue dropped and the transform job failed"
))
print(report.model_dump_json(indent=2))
