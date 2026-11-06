"""Strict read-only diagnostic tools. No model-controlled URLs, SQL or shell."""
from __future__ import annotations

from copy import deepcopy

from .models import ToolName

_FIXTURES = {
    "daily_revenue_etl": {
        ToolName.STATUS: {
            "last_run": "failed", "failed_task": "transform_revenue",
            "record_count_change_pct": -32, "upstream": "order_events"
        },
        ToolName.LOGS: {
            "lines": [
                "2026-11-06 07:05:11 ERROR transform_revenue: column 'order_amount' does not exist",
                "2026-11-06 07:05:11 ERROR job exited with code 1"
            ]
        },
        ToolName.SCHEMA: {
            "source_table": "order_events",
            "removed_columns": ["order_amount"],
            "added_columns": ["total_amount"],
            "observed_at": "2026-11-06T06:58:00Z"
        },
        ToolName.RUNBOOK: {
            "runbook_id": "RB-SCHEMA-001", "version": "1.2",
            "recommended_review": "Review column mapping, test in staging, then consider a controlled pipeline rerun"
        }
    },
    "customer_orders_hourly": {
        ToolName.STATUS: {
            "last_run": "delayed", "failed_task": "extract_orders",
            "record_count_change_pct": -8, "upstream": "orders_api"
        },
        ToolName.LOGS: {
            "lines": ["2026-11-06 07:00:00 WARN upstream event batch arrived late"]
        },
        ToolName.SCHEMA: {
            "source_table": "order_events", "removed_columns": [], "added_columns": []
        },
        ToolName.RUNBOOK: {
            "runbook_id": "RB-FRESH-002", "version": "1.0",
            "recommended_review": "Check upstream delivery lag and freshness SLA"
        }
    }
}


class ToolDenied(ValueError):
    pass


def execute_readonly_tool(name: str, pipeline_id: str) -> dict:
    """Enforce a fixed, typed allowlist at the backend boundary."""
    try:
        tool_name = ToolName(name)
    except ValueError as exc:
        raise ToolDenied(f"Tool not on read-only allowlist: {name}") from exc
    if pipeline_id not in _FIXTURES:
        raise ToolDenied("Pipeline not available to this local demo")
    # Return fresh data so no caller can mutate the fixture.
    return deepcopy(_FIXTURES[pipeline_id][tool_name])


def authorized_tools() -> list[str]:
    return [t.value for t in ToolName]
