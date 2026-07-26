# Overview-agent contract

Use one independent overview subagent alongside all task-detail subagents. Dispatch it first so task fan-out cannot consume its slot. The coordinator must return after dispatch, so this worker owns the asynchronous whole-system scan.

## Assignment

Give the overview agent the goal, repository root, repository guidance, routing-plan path, and output directory. Ask it to inspect the broad architecture, representative entry points, schemas, interfaces, and cross-boundary flows deeply enough to explain the system as a whole.

Do not decompose work, draft task prompts, or propose a DAG. Do not read task prompt files or task-detail results. Keep the repository read-only so reconciliation receives an independent global view.

## Result

```json
{
  "summary": "How the relevant system works as a whole.",
  "system_boundaries": ["Boundary and responsibility"],
  "end_to_end_flows": ["Input → processing → output"],
  "shared_invariants": ["Rule every local task must preserve"],
  "integration_surfaces": ["Cross-boundary contract"],
  "global_risks": ["Whole-system risk"],
  "unknowns": ["Question that source inspection did not settle"]
}
```

Do not include `tasks`, `lanes`, `modules`, `dependencies`, or `collisions`.

Write the JSON to a unique temporary path, then run:

```text
scripts/land_system_overview.py <plan.json> <overview.json> --output-dir <task-directory>
```

The script atomically replaces `00-system-overview.md`. A successful landing needs no coordinator response.
