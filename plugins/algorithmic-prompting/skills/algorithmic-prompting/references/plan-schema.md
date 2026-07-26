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
      "input": "Approved authentication contract",
      "paths": ["api/**"],
      "output": "Tested authentication endpoint",
      "validation": ["run API tests"],
      "base_branch": "feature/authentication",
      "assigned_branch": "task/authentication/api"
    },
    {
      "id": "SDK",
      "scope": "Client library and exported types",
      "input": "Approved authentication contract",
      "paths": ["sdk/**"],
      "output": "Tested authentication client",
      "validation": ["run SDK tests"],
      "base_branch": "feature/authentication",
      "assigned_branch": "task/authentication/sdk"
    },
    {
      "id": "WEB",
      "scope": "Browser UI and interactions",
      "input": "Approved UI behavior and authentication contract",
      "paths": ["web/**"],
      "output": "Connected sign-in flow",
      "validation": ["run sign-in UI tests"],
      "base_branch": "feature/authentication",
      "assigned_branch": "task/authentication/web"
    },
    {
      "id": "INT",
      "scope": "Cross-layer authentication verification",
      "input": "Integrated API, SDK, and Web lane outputs",
      "paths": ["tests/integration/auth/**"],
      "output": "Verified end-to-end authentication flow",
      "validation": ["run authentication integration tests"],
      "base_branch": "feature/authentication",
      "assigned_branch": "task/authentication/int"
    }
  ],
  "tasks": [
    {
      "id": "API-01",
      "lane": "API",
      "title": "Validate authentication requests",
      "commit_intent": "Validate authentication requests",
      "status": "planned",
      "files": ["api/auth.ts", "api/auth.test.ts"],
      "validation": ["run focused request-validation tests"],
      "completion_gate": "Request-validation tests pass",
      "assigned_branch": "task/authentication/api",
      "draft_prompt": "Implement API-01 in the API lane..."
    },
    {
      "id": "API-02",
      "lane": "API",
      "title": "Issue authenticated sessions",
      "commit_intent": "Issue authenticated sessions",
      "status": "planned",
      "files": ["api/auth.ts", "api/auth.test.ts"],
      "validation": ["run focused session tests"],
      "completion_gate": "Session issuance tests pass",
      "assigned_branch": "task/authentication/api",
      "draft_prompt": "Implement API-02 after API-01 on the API lane branch..."
    },
    {
      "id": "SDK-01",
      "lane": "SDK",
      "title": "Add the authentication client",
      "commit_intent": "Add the authentication client",
      "status": "planned",
      "files": ["sdk/auth.ts"],
      "validation": ["run focused SDK tests"],
      "completion_gate": "SDK authentication tests pass",
      "assigned_branch": "task/authentication/sdk",
      "draft_prompt": "Implement SDK-01 in the SDK lane after API-01 is available..."
    },
    {
      "id": "WEB-01",
      "lane": "WEB",
      "title": "Connect the sign-in form",
      "commit_intent": "Connect the sign-in form",
      "status": "planned",
      "files": ["web/sign-in.tsx"],
      "validation": ["run focused sign-in UI tests"],
      "completion_gate": "Sign-in UI tests pass",
      "assigned_branch": "task/authentication/web",
      "draft_prompt": "Implement the complete WEB lane using the approved contract..."
    },
    {
      "id": "INT-01",
      "lane": "INT",
      "title": "Verify the integrated authentication flow",
      "commit_intent": "Verify the integrated authentication flow",
      "status": "planned",
      "files": ["tests/integration/auth/**"],
      "validation": ["run authentication integration tests"],
      "completion_gate": "End-to-end authentication tests pass",
      "assigned_branch": "task/authentication/int",
      "draft_prompt": "Verify the integrated API, SDK, and Web lane outputs..."
    }
  ],
  "dependencies": [
    {"from": "API-01", "to": "API-02", "reason": "Session issuance builds on request validation"},
    {"from": "API-02", "to": "INT-01", "reason": "Integration consumes the API output"},
    {"from": "SDK-01", "to": "INT-01", "reason": "Integration consumes the SDK output"},
    {"from": "WEB-01", "to": "INT-01", "reason": "Integration consumes the Web output"}
  ],
  "collisions": []
}
```

## Field rules

- Define a small number of broad lanes. Give each lane a unique uppercase alphanumeric `id`, input, scope, owned paths or components, output, validation profile, base branch, and assigned child branch.
- Treat each lane as the default worktree and merge unit. Split it into the fewest atomic commit units that make the history reviewable and revertible, usually one to three.
- Map every task one-to-one to a commit and record a human-readable `commit_intent` without its coordination ID. Split for independently meaningful behavior, a prerequisite, owner handoff, merge or rollback boundary, or validation gate—not for routine steps or individual files.
- Keep implementation and its focused tests together. Avoid standalone scaffolding, formatting, generated-output, or test-only commits unless independently valuable.
- Add `modules` only when one lane contains multiple independently mergeable outputs. Give each module a stable uppercase kebab ID, one lane, an input contract, ownership, validation, and output. When modules exist, assign every task to one in the same lane.
- Keep task IDs unique and stable in `<LANE>-<NN>` form. The task's `lane` must match its ID prefix and reference a declared lane.
- Use `CORE` for a plan where no meaningful multi-lane partition exists.
- Express prerequisites only in `dependencies`; scripts derive the lane and optional module DAGs by collapsing task edges.
- Derive the module DAG by collapsing cross-module task dependencies. Do not duplicate those edges in a separate module dependency list.
- Derive lane branches as `task/<goal-slug>/<lane-id-lower>` and validate the final Git ref before dispatch. Use a task suffix only for an intentionally separate task worktree.
- Give every task a non-empty `draft_prompt` that follows `coding-agent-prompt.md`. The approved dispatch prompt must end successful work with one focused commit whose outcome-based subject and bullet body omit internal graph identifiers.
- Use statuses `planned`, `ready`, `active`, `completed`, `integrated`, or `blocked`.
- Treat `completed` and `integrated` tasks as removed for Kahn indegree calculations. Choose `integrated` when downstream tasks require the result on their base branch.
- Represent prerequisites only in `dependencies`. Each edge is directed from prerequisite to successor.
- Represent file overlap and merge risk only in `collisions`; these do not affect indegrees.
- Omit `integration_order` when the order needs a human decision.
- Keep dependency and collision reasons specific enough for review.
