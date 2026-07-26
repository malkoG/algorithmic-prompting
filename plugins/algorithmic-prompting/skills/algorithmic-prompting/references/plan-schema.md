# Plan JSON schema

Use this shape when persisting a plan. Replace the neutral lane names with boundaries from the project.

```json
{
  "goal": "Deliver the requested change",
  "goal_slug": "requested-change",
  "lanes": [
    {
      "id": "PART1",
      "scope": "First independent responsibility",
      "input": "Accepted requirements",
      "paths": ["path/owned/by/part-one/**"],
      "output": "Validated first output",
      "validation": ["run checks for the first responsibility"],
      "base_branch": "main",
      "assigned_branch": "task/requested-change/part1"
    },
    {
      "id": "PART2",
      "scope": "Second independent responsibility",
      "input": "Accepted requirements",
      "paths": ["path/owned/by/part-two/**"],
      "output": "Validated second output",
      "validation": ["run checks for the second responsibility"],
      "base_branch": "main",
      "assigned_branch": "task/requested-change/part2"
    },
    {
      "id": "VERIFY",
      "scope": "Combined verification",
      "input": "Integrated outputs from PART1 and PART2",
      "paths": ["path/owned/by/verification/**"],
      "output": "Verified combined result",
      "validation": ["run combined checks"],
      "base_branch": "main",
      "assigned_branch": "task/requested-change/verify"
    }
  ],
  "tasks": [
    {
      "id": "PART1-01",
      "lane": "PART1",
      "title": "Produce the first atomic outcome",
      "commit_intent": "Produce the first atomic outcome",
      "status": "planned",
      "files": ["path/owned/by/part-one/**"],
      "validation": ["run focused checks"],
      "completion_gate": "Focused checks pass",
      "assigned_branch": "task/requested-change/part1",
      "draft_prompt": "Complete the first atomic outcome and its focused validation."
    },
    {
      "id": "PART2-01",
      "lane": "PART2",
      "title": "Produce the second atomic outcome",
      "commit_intent": "Produce the second atomic outcome",
      "status": "planned",
      "files": ["path/owned/by/part-two/**"],
      "validation": ["run focused checks"],
      "completion_gate": "Focused checks pass",
      "assigned_branch": "task/requested-change/part2",
      "draft_prompt": "Complete the second atomic outcome and its focused validation."
    },
    {
      "id": "VERIFY-01",
      "lane": "VERIFY",
      "title": "Verify the combined result",
      "commit_intent": "Verify the combined result",
      "status": "planned",
      "files": ["path/owned/by/verification/**"],
      "validation": ["run combined checks"],
      "completion_gate": "Combined checks pass",
      "assigned_branch": "task/requested-change/verify",
      "draft_prompt": "Verify the integrated outputs."
    }
  ],
  "dependencies": [
    {
      "from": "PART1-01",
      "to": "VERIFY-01",
      "reason": "Combined verification consumes the first output"
    },
    {
      "from": "PART2-01",
      "to": "VERIFY-01",
      "reason": "Combined verification consumes the second output"
    }
  ],
  "collisions": []
}
```

## Rules

- Lane IDs are unique uppercase alphanumeric names derived from project boundaries.
- Each lane has a scope, predicted paths or components, validation profile, input, and output.
- Task IDs use `<LANE>-<NN>` and reference a declared lane.
- Each task maps to one atomic commit and has a commit intent, validation, completion gate, and draft prompt.
- Status is `planned`, `ready`, `active`, `completed`, `integrated`, or `blocked`.
- Dependencies point from prerequisite to successor.
- Only incomplete prerequisite edges contribute to readiness. `completed` and `integrated` predecessors are removed.
- Collisions describe overlap or merge risk and do not change indegrees.
- Use one branch and worktree per lane by default. Use a task-specific branch only for independently dispatched work.
- Optional modules may group multiple mergeable outputs inside a large lane. When modules exist, every task references a module in the same lane.
- Derive lane and optional module graphs from task dependencies; do not duplicate edges.
- Omit unresolved integration order and ask the human instead.
