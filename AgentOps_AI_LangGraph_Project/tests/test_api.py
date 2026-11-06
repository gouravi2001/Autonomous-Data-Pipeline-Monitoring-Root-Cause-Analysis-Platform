from fastapi.testclient import TestClient
from agentops.main import make_app
from agentops.store import Store


def test_end_to_end_local_review(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = TestClient(make_app(Store(str(tmp_path / "test.sqlite3"))))
    created = client.post("/incidents", json={
        "pipeline_id": "daily_revenue_etl", "description": "Revenue totals dropped"
    })
    assert created.status_code == 201
    incident_id = created.json()["id"]
    assert client.get(f"/incidents/{incident_id}").json()["status"] == "pending_review"
    reviewed = client.post(f"/incidents/{incident_id}/review", json={
        "reviewer": "demo-engineer", "decision": "approve", "comment": "Tested in demo"
    })
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "approved_in_simulation"
    assert client.post(f"/incidents/{incident_id}/review", json={
        "reviewer": "demo-engineer", "decision": "approve"
    }).status_code == 409
    audit = client.get(f"/incidents/{incident_id}/audit").json()
    assert [e["action"] for e in audit] == ["investigated", "simulated_approve"]


def test_reject_unauthorized_pipeline(tmp_path):
    client = TestClient(make_app(Store(str(tmp_path / "test.sqlite3"))))
    resp = client.post("/incidents", json={"pipeline_id": "production_private_db", "description": "Look at everything"})
    assert resp.status_code == 422
