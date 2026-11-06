FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir ".[langgraph]"
RUN useradd --create-home --uid 10001 agentops
USER agentops
ENV PYTHONPATH=/app/src AGENTOPS_DB_PATH=/tmp/agentops.sqlite3
EXPOSE 8000
CMD ["uvicorn", "agentops.main:app", "--host", "0.0.0.0", "--port", "8000"]
