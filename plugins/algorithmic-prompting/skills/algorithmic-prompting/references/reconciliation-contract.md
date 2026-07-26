# Reconciliation contract

Run reconciliation only on a later invocation after the system overview and all task prompts have landed. Reconciliation belongs to the main thread.

Read the shared plan, system overview, task detail results, and task files. Compare global understanding with local execution guidance. Do not re-scan the repository unless an artifact reports an unresolved contradiction.

Produce:

```json
{
  "summary": "Whether the global and local views agree.",
  "global_constraints": ["Constraint every affected task must preserve"],
  "proposals": [
    {
      "kind": "task",
      "action": "amend",
      "targets": ["DOMAIN-01"],
      "reason": "The overview exposes a cross-boundary requirement."
    }
  ],
  "human_decisions": ["Approve or reject the proposed task amendment"]
}
```

Proposal kinds are `task`, `dependency`, or `collision`. Actions are `confirm`, `amend`, `add`, `remove`, `merge`, or `split`.

Land the report with:

```text
scripts/land_reconciliation.py <plan.json> <reconciliation.json> --output-dir <task-directory>
```

The report is advisory. Do not modify the shared plan, task prompts, or ready queue until the human approves the proposals. After approval, update the plan explicitly, rerun graph validation, and resume Kahn's algorithm.
