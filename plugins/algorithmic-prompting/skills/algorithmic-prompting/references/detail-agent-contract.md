# Detail-agent contract

Use one independent subagent per prompt-detail task after the index and placeholders exist. Dispatch all of them concurrently; the coordinator returns immediately after dispatch.

## Assignment

Give the detail agent the shared routing-plan path, output directory, assigned task ID, lane scope, repository guidance, visible layout evidence, and explicit prerequisites. It owns the implementation, test, SDK, UI, and documentation inspection needed to make the task executable.

Verify routing assumptions against actual code. Report uncertainties and proposed dependency or collision corrections. This is read-only planning. Do not edit the repository, create branches or worktrees, implement code, commit, or modify the shared plan, index, manifest, or sibling files.

## Compact result

Return only the task-specific delta. The landing script supplies shared context, branch safety, commit rules, and handoff boilerplate.

```json
{
  "task_id": "DOMAIN-01",
  "guidance": "Task-specific implementation judgment.",
  "scope": ["Atomic responsibility"],
  "files": ["path/or/component"],
  "done": ["Observable completion condition"],
  "checks": ["Focused check"]
}
```

Add these fields only when needed: `profile`, `context`, `out_of_scope`, `completion_gate`, `risks`, `proposed_dependencies`, `proposed_collisions`, and `uncertainties`. The landing script still accepts the earlier verbose schema for compatibility.

Follow the size budget in [prompt-profiles.md](prompt-profiles.md). Never repeat plan facts or execution boilerplate in `guidance`.

## Land the task file

Write the JSON to a unique temporary path, then run:

```text
scripts/land_task_detail.py <plan.json> <detail.json> --output-dir <task-directory>
```

The script validates the result, compiles the prompt, atomically replaces only that placeholder, and stores the original compact result under `.task-details/`. A successful landing needs no coordinator response.

Do not update the index. Leave graph proposals and uncertainties in the task file for later human review. On inspection or landing failure, leave the placeholder intact and report through the detail job's own status surface.
