# AgentOps AI — Agentic Data Reliability & Incident Response Platform

An **implementable multi-agent AI project** for diagnosing data pipeline incidents. The project includes six agent functions, two orchestration options, a simulated data platform, evidence-based diagnosis, human review, a small UI, unit tests, and a conditional **real LangGraph `StateGraph`**.

**Safety/scope:** This is a local synthetic-data portfolio demo, not a deployed enterprise system. The approval screen only records simulated decisions. No agent can run arbitrary SQL, shell commands, fetch arbitrary URLs, or modify production systems.

## Technology used

| What | Technology | Status |
|---|---|---|
| Agent workflow | **LangGraph StateGraph** | Implemented as an optional runtime in `src/agentops/langgraph_workflow.py` |
| LLM tool decision + diagnosis | Configurable OpenAI-compatible HTTP API, typed with Pydantic | Optional; disabled by default |
| Structured agent models | Pydantic | Implemented |
| API/backend | Python + FastAPI | Implemented |
| Demo persistence/auditing | SQLite | Implemented |
| Dashboard | HTML/CSS/vanilla JavaScript | Implemented |
| Testing | Pytest | Implemented |
| Docker | Dockerfile + Compose | Implemented (local demo) |
| LangGraph pause/resume | `interrupt`, `Command`, `InMemorySaver` | Separate educational example; not wired to the API |
| LangChain Core retrieval + toy vector store | Small offline retrieval module | Implemented in `langchain_retrieval.py` when optional dependencies are installed |
| pgvector + PostgreSQL + OpenTelemetry + Kubernetes | Production extension design | **Not yet implemented** |

## Folder tree

```text
AgentOps_AI_LangGraph_Project/
├── src/agentops/
│   ├── agents.py                  # Six agent responsibilities
│   ├── langgraph_workflow.py      # Actual StateGraph nodes + policy routing
│   ├── langchain_retrieval.py      # Local LangChain vector-retrieval demonstration
│   ├── workflow.py                # Pure-Python fallback orchestrator
│   ├── llm.py                     # Optional bounded LLM tool selection
│   ├── tools.py                   # Read-only diagnostic tool allowlist
│   ├── models.py                  # Pydantic request/output schemas
│   ├── store.py                   # Incident storage and audit
│   ├── main.py                    # FastAPI routes
│   └── static/dashboard.html      # Browser UI
├── examples/
│   ├── run_langgraph.py           # Direct graph invocation
│   └── human_review_interrupt.py  # Pause and resume review example
├── tests/                         # Unit, API and security tests
├── docs/                          # Architecture and evaluation plan
├── .github/workflows/tests.yml    # GitHub Actions CI
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

## Run the real LangGraph workflow

Python 3.11 or newer:

```bash
python -m venv .venv
source .venv/bin/activate             # Windows: .venv\Scripts\activate
pip install -e '.[langgraph,dev]'
export AGENTOPS_ENGINE=langgraph      # Windows PowerShell: $env:AGENTOPS_ENGINE='langgraph'
uvicorn agentops.main:app --reload
```

Then open `http://127.0.0.1:8000/demo` or API docs at `http://127.0.0.1:8000/docs`.

Run the LangGraph graph without the API:

```bash
python examples/run_langgraph.py
```

Demonstrate checkpointed human review via **actual LangGraph** `interrupt` and `Command` (in-memory, not the API's SQLite reviewer flow):

```bash
python examples/human_review_interrupt.py
```

## Run without installing LangGraph

If you only want to explore the API and UI, a pure-Python sequence runs the same agent functions:

```bash
pip install -e '.[dev]'
export AGENTOPS_ENGINE=python         # Default if unset
uvicorn agentops.main:app --reload
```

## Test

```bash
pytest -q
```

The LangGraph tests in `tests/test_langgraph.py` are skipped when LangGraph is unavailable. To test them, first install the `[langgraph]` extra.

## Example API

```bash
curl -X POST http://127.0.0.1:8000/incidents \
  -H 'Content-Type: application/json' \
  -d '{"pipeline_id":"daily_revenue_etl","description":"Revenue totals dropped unexpectedly"}'
```

The JSON response contains an `id`, evidence objects, diagnosis, proposed action, and `pending_review` status. Use the ID to read the report:

```bash
curl http://127.0.0.1:8000/incidents/INCIDENT_ID
```

To record review **in simulation only**:

```bash
curl -X POST http://127.0.0.1:8000/incidents/INCIDENT_ID/review \
  -H 'Content-Type: application/json' \
  -d '{"reviewer":"demo-engineer","decision":"approve","comment":"Local simulation"}'
```

## Realistic next steps

1. Connect read-only Airflow and dbt status/log APIs and a PostgreSQL metadata database; replace hard-coded diagnostic fixtures.
2. Add tenant-scoped LangChain retrievers and a pgvector-backed runbook/history index; evaluate grounded retrieval.
3. Replace toy hashed-token embeddings with real evaluated multilingual embeddings, and the local vector store with tenant-scoped pgvector. Use a durable LangGraph PostgreSQL checkpointer, authenticated review flow, queue workers, and idempotent incident ingestion.
4. Add OpenTelemetry traces and metrics, rate limits, secrets management, RBAC, and staging chaos/replay tests.
5. Build a **separate** highly restricted, human-authorized execution service; do not let a model directly perform writes.

See `docs/architecture.md` and `docs/evaluation.md` for design and scoring criteria.
