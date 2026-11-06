"""Local-only demo. No authentication: NEVER deploy on a public interface."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pathlib import Path
import os
from .models import IncidentRequest, ReviewRequest, InvestigationReport
from .store import ConflictError, Store
from .workflow import investigate


def make_app(store: Store | None = None) -> FastAPI:
    app = FastAPI(title="AgentOps AI (synthetic local demo)", version="0.1.0")
    app.state.store = store or Store()

    @app.get("/demo", response_class=HTMLResponse, include_in_schema=False)
    def demo_dashboard():
        return (Path(__file__).parent / "static" / "dashboard.html").read_text(encoding="utf-8")

    @app.get("/health")
    def health():
        return {"status": "ok", "environment": "local-synthetic-demo"}

    @app.post("/incidents", response_model=InvestigationReport, status_code=201)
    def create_incident(request: IncidentRequest):
        engine = os.getenv("AGENTOPS_ENGINE", "python").lower().strip()
        if engine == "langgraph":
            from .langgraph_workflow import run_graph
            report = run_graph(request)
        elif engine == "python":
            report = investigate(request)
        else:
            raise HTTPException(status_code=500, detail="Invalid AGENTOPS_ENGINE setting")
        app.state.store.add(report)
        return report

    @app.get("/incidents/{incident_id}", response_model=InvestigationReport)
    def get_incident(incident_id: str):
        report = app.state.store.get(incident_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Incident not found")
        return report

    @app.post("/incidents/{incident_id}/review", response_model=InvestigationReport)
    def review_incident(incident_id: str, request: ReviewRequest):
        try:
            report = app.state.store.review(incident_id, request)
        except ConflictError as err:
            raise HTTPException(status_code=409, detail=str(err)) from err
        if report is None:
            raise HTTPException(status_code=404, detail="Incident not found")
        return report

    @app.get("/incidents/{incident_id}/audit")
    def incident_audit(incident_id: str):
        if app.state.store.get(incident_id) is None:
            raise HTTPException(status_code=404, detail="Incident not found")
        return app.state.store.audit(incident_id)

    return app


app = make_app()
