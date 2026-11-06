# Evaluation plan

Create a versioned benchmark set with >=100 synthetic incidents across known
root causes: schema drift, freshness, duplicates, missing partitions, permissions,
warehouse performance and upstream source failure. Include ambiguous and no-fault
cases. Blindly label each with evidence, required tool sequence, safe/unsafe
suggestions and permitted reviewer actions.

Measure:

- **Root-cause top-1 accuracy:** correct causal category / all labeled cases.
- **Evidence grounding:** supported cited evidence IDs / all cited IDs.
- **Tool-use precision:** required diagnostic calls / total diagnostic calls.
- **False-automation rate:** unauthorized real-world writes / all runs; target 0.
- **Escalation recall:** high-uncertainty or unsafe cases flagged / unsafe cases.
- **Latency p50/p95**, LLM tokens and cost per investigated incident.
- **Recovery quality:** accuracy after tool timeout, partial logs, malformed JSON,
  prompt injection attempts, checkpoint recovery, duplicate events, API retries.

Maintain separate unit, integration, replay, prompt-injection, and staging
chaos-test suites. Before changing the model or prompts, run the same golden
set and publish a before/after comparison with confidence intervals.

Service-level objectives are **project targets**, not achieved results:
- 100% simulated approval gate coverage in unit and integration tests
- >90% evidence ID validity on the evaluation benchmark
- 0 unapproved production actions
- p95 investigation latency <30 s in staging with bounded tool calls
