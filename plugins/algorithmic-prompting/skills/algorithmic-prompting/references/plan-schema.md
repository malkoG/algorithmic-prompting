# Plan JSON schema

Use this compact shape when a persistent or script-validated plan is useful:

```json
{
  "goal": "Ship the requested change",
  "goal_slug": "authentication",
  "lanes": [
    {
      "id": "API",
      "scope": "Server endpoints and contracts",
      "paths": ["api/**"],
      "validation": ["run API tests"]
    },
    {
      "id": "SDK",
      "scope": "Client library and exported types",
      "paths": ["sdk/**"],
      "validation": ["run SDK tests"]
    },
    {
      "id": "WEB",
      "scope": "Browser UI and interactions",
      "paths": ["web/**"],
      "validation": ["run Web tests"]
    }
  ],
  "modules": [
    {
      "id": "API-AUTH",
      "lane": "API",
      "input": "Approved authentication contract",
      "owns": ["api/auth/**"],
      "output": "Tested authentication endpoint",
      "validation": ["run authentication API tests"],
      "status": "completed",
      "base_branch": "feature/authentication",
      "assigned_branch": "task/authentication/api-auth"
    },
    {
      "id": "SDK-AUTH",
      "lane": "SDK",
      "input": "Integrated authentication API",
      "owns": ["sdk/auth/**"],
      "output": "Tested authentication client",
      "validation": ["run authentication SDK tests"],
      "status": "planned",
      "base_branch": "feature/authentication",
      "assigned_branch": "task/authentication/sdk-auth"
    },
    {
      "id": "WEB-AUTH",
      "lane": "WEB",
      "input": "Integrated authentication client",
      "owns": ["web/sign-in/**"],
      "output": "Connected sign-in flow",
      "validation": ["run sign-in UI tests"],
      "status": "planned",
      "base_branch": "feature/authentication",
      "assigned_branch": "task/authentication/web-auth"
    }
  ],
  "tasks": [
    {
      "id": "API-01",
      "lane": "API",
      "module": "API-AUTH",
      "title": "Expose the authentication endpoint",
      "status": "completed",
      "files": ["api/auth.ts"],
      "validation": ["run focused authentication API tests"],
      "completion_gate": "Authentication API tests pass",
      "assigned_branch": "task/authentication/api-01-add-endpoint",
      "draft_prompt": "Implement API-01 in the API lane..."
    },
    {
      "id": "SDK-01",
      "lane": "SDK",
      "module": "SDK-AUTH",
      "title": "Add the authentication client",
      "status": "planned",
      "files": ["sdk/auth.ts"],
      "validation": ["run focused SDK tests"],
      "completion_gate": "SDK authentication tests pass",
      "assigned_branch": "task/authentication/sdk-01-add-client",
      "draft_prompt": "Implement SDK-01 in the SDK lane after API-01 is available..."
    },
    {
      "id": "WEB-01",
      "lane": "WEB",
      "module": "WEB-AUTH",
      "title": "Connect the sign-in form",
      "status": "planned",
      "files": ["web/sign-in.tsx"],
      "validation": ["run focused sign-in UI tests"],
      "completion_gate": "Sign-in UI tests pass",
      "assigned_branch": "task/authentication/web-01-connect-sign-in",
      "draft_prompt": "Implement WEB-01 in the WEB lane after SDK-01 is available..."
    }
  ],
  "dependencies": [
    {"from": "API-01", "to": "SDK-01", "reason": "SDK consumes the API contract"},
    {"from": "SDK-01", "to": "WEB-01", "reason": "Web integration consumes the SDK client"}
  ],
  "collisions": []
}
```

## Field rules

- Define at least one lane. Give each lane a unique uppercase alphanumeric `id`, a scope, likely paths or components, and a validation profile.
- Add `modules` when work can be parallelized as independently mergeable units. Give each module a stable uppercase kebab ID, one lane, an input contract, exclusive ownership, independent validation, and one mergeable output.
- Treat lanes as architectural partitions, modules as worktree and merge units, and tasks as the smallest verifiable implementation steps. A module may contain a local task DAG.
- When `modules` exists, assign every task to a declared module in the same lane. Omit `modules` for simple task-only plans.
- Keep task IDs unique and stable in `<LANE>-<NN>` form. The task's `lane` must match its ID prefix and reference a declared lane.
- Use `CORE` for a plan where no meaningful multi-lane partition exists.
- Treat lanes as metadata, not dependencies. Express every cross-lane prerequisite in `dependencies`.
- Derive the module DAG by collapsing cross-module task dependencies. Do not duplicate those edges in a separate module dependency list.
- Assign one branch and worktree per ready module by default. Use per-task worktrees only when tasks inside the module are genuinely independent and have disjoint ownership.
- Derive module branches as `task/<goal-slug>/<module-id-lower>` unless a more specific collision-free name is needed.
- Derive assigned branches as `task/<goal-slug>/<task-id-lower>-<task-slug>` and validate the final Git ref before dispatch.
- Give every task a non-empty `draft_prompt` that follows `coding-agent-prompt.md`.
- Use statuses `planned`, `ready`, `active`, `completed`, `integrated`, or `blocked`.
- Treat `completed` and `integrated` tasks as removed for Kahn indegree calculations. Choose `integrated` when downstream tasks require the result on their base branch.
- Represent prerequisites only in `dependencies`. Each edge is directed from prerequisite to successor.
- Represent file overlap and merge risk only in `collisions`; these do not affect indegrees.
- Omit `integration_order` when the order needs a human decision.
- Keep dependency and collision reasons specific enough for review.
