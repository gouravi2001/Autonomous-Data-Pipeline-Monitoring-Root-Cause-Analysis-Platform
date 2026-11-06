"""SQLite local-demo incident persistence; use PostgreSQL in production."""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from .models import InvestigationReport, ReviewRequest


class ConflictError(RuntimeError):
    pass


class Store:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or os.getenv("AGENTOPS_DB_PATH", "./agentops.sqlite3")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS incidents (
                  id TEXT PRIMARY KEY, status TEXT NOT NULL, data TEXT NOT NULL,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS audits (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  incident_id TEXT NOT NULL, action TEXT NOT NULL, actor TEXT NOT NULL,
                  notes TEXT NOT NULL DEFAULT '', at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=5.0)

    def add(self, report: InvestigationReport) -> None:
        with self._connect() as conn:
            conn.execute("INSERT INTO incidents(id,status,data) VALUES (?,?,?)",
                         (report.id, report.status, report.model_dump_json()))
            conn.execute("INSERT INTO audits(incident_id,action,actor,notes) VALUES (?,?,?,?)",
                         (report.id, "investigated", "agentops-system", report.mode))

    def get(self, incident_id: str) -> InvestigationReport | None:
        with self._connect() as conn:
            row = conn.execute("SELECT data FROM incidents WHERE id=?", (incident_id,)).fetchone()
        return InvestigationReport.model_validate_json(row[0]) if row else None

    def review(self, incident_id: str, request: ReviewRequest) -> InvestigationReport | None:
        """Record simulation outcome. Never executes a remediation action."""
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT data,status FROM incidents WHERE id=?", (incident_id,)).fetchone()
            if row is None:
                return None
            if row[1] != "pending_review":
                raise ConflictError("Incident already reviewed; no duplicate approvals")
            report = InvestigationReport.model_validate_json(row[0])
            report.status = "approved_in_simulation" if request.decision == "approve" else "rejected_in_simulation"
            conn.execute("UPDATE incidents SET status=?,data=? WHERE id=?",
                         (report.status, report.model_dump_json(), incident_id))
            conn.execute("INSERT INTO audits(incident_id,action,actor,notes) VALUES (?,?,?,?)",
                         (incident_id, f"simulated_{request.decision}", request.reviewer, request.comment))
        return report

    def audit(self, incident_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT action,actor,notes,at FROM audits WHERE incident_id=? ORDER BY id",
                                (incident_id,)).fetchall()
        return [dict(action=r[0], actor=r[1], notes=r[2], at=r[3]) for r in rows]
