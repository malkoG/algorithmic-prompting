# Plan JSON schema

Use this shape when persisting a plan. This example uses compiler boundaries to make lane ownership concrete; derive names from the actual project.

```json
{
  "goal": "Add a language feature",
  "goal_slug": "language-feature",
  "topology_status": "provisional",
  "prompt_profile": "lean",
  "lanes": [
    {
      "id": "PARSER",
      "scope": "Syntax recognition",
      "input": "Accepted grammar and syntax-tree contract",
      "paths": ["compiler/parser/**"],
      "output": "Parsed representation of the new syntax",
      "validation": ["run parser tests"],
      "base_branch": "main",
      "assigned_branch": "task/language-feature/parser"
    },
    {
      "id": "CHECKER",
      "scope": "Semantic analysis",
      "input": "Accepted semantic rules and typed-representation contract",
      "paths": ["compiler/checker/**"],
      "output": "Validated semantics for the new construct",
      "validation": ["run semantic-analysis tests"],
      "base_branch": "main",
      "assigned_branch": "task/language-feature/checker"
    },
    {
      "id": "EMITTER",
      "scope": "Output generation",
      "input": "Accepted output semantics and intermediate-representation contract",
      "paths": ["compiler/emitter/**"],
      "output": "Generated output for the new construct",
      "validation": ["run emitter tests"],
      "base_branch": "main",
      "assigned_branch": "task/language-feature/emitter"
    },
    {
      "id": "VERIFY",
      "scope": "Integrated language behavior",
      "input": "Integrated parser, checker, and emitter outputs",
      "paths": ["compiler/integration-tests/**"],
      "output": "Verified end-to-end language feature",
      "validation": ["run language integration tests"],
      "base_branch": "main",
      "assigned_branch": "task/language-feature/verify"
    }
  ],
  "tasks": [
    {
      "id": "PARSER-01",
      "lane": "PARSER",
      "title": "Recognize the new syntax",
      "commit_intent": "Recognize the new syntax",
      "status": "planned",
      "files": ["compiler/parser/**"],
      "validation": ["run focused parser tests"],
      "completion_gate": "Focused parser tests pass",
      "assigned_branch": "task/language-feature/parser",
      "prompt_seed": "Recognize the new syntax and preserve existing recovery behavior. Cover accepted and rejected forms with focused parser tests."
    },
    {
      "id": "CHECKER-01",
      "lane": "CHECKER",
      "title": "Validate the new semantics",
      "commit_intent": "Validate the new semantics",
      "status": "planned",
      "files": ["compiler/checker/**"],
      "validation": ["run focused semantic-analysis tests"],
      "completion_gate": "Focused semantic-analysis tests pass",
      "assigned_branch": "task/language-feature/checker",
      "prompt_seed": "Validate the new semantics against the accepted representation contract and preserve existing diagnostics."
    },
    {
      "id": "EMITTER-01",
      "lane": "EMITTER",
      "title": "Emit the new construct",
      "commit_intent": "Emit the new construct",
      "status": "planned",
      "files": ["compiler/emitter/**"],
      "validation": ["run focused emitter tests"],
      "completion_gate": "Focused emitter tests pass",
      "assigned_branch": "task/language-feature/emitter",
      "prompt_seed": "Emit the new construct against the accepted output contract without changing unrelated output."
    },
    {
      "id": "VERIFY-01",
      "lane": "VERIFY",
      "title": "Verify the language feature",
      "commit_intent": "Verify the language feature",
      "status": "planned",
      "files": ["compiler/integration-tests/**"],
      "validation": ["run language integration tests"],
      "completion_gate": "Language integration tests pass",
      "assigned_branch": "task/language-feature/verify",
      "prompt_seed": "Verify the integrated parser, checker, and emitter outputs across successful and rejected programs."
    }
  ],
  "dependencies": [
    {
      "from": "PARSER-01",
      "to": "VERIFY-01",
      "reason": "Integrated verification consumes parsed syntax"
    },
    {
      "from": "CHECKER-01",
      "to": "VERIFY-01",
      "reason": "Integrated verification consumes semantic validation"
    },
    {
      "from": "EMITTER-01",
      "to": "VERIFY-01",
      "reason": "Integrated verification consumes generated output"
    }
  ],
  "collisions": []
}
```

## Rules

- Lane IDs are unique uppercase alphanumeric names derived from project boundaries.
- Use `topology_status: provisional` for the initial map-first plan. Promote it only after graph evidence has been reviewed.
- Each lane has a scope, predicted paths or components, validation profile, input, and output.
- Task IDs use `<LANE>-<NN>` and reference a declared lane.
- `prompt_profile` is `lean` by default, or `balanced` / `thorough`. A task may override the plan profile.
- Each task maps to one atomic commit and has a commit intent, validation, completion gate, and `prompt_seed`.
- `prompt_seed` holds only task-specific implementation judgment. The renderer adds the full lane, dependency, scope, branch, validation, commit, and handoff contract.
- Each detail job supplies the compact `guidance`, `scope`, `files`, `done`, and `checks` delta when atomically replacing its placeholder.
- Legacy plans using `draft_prompt` remain accepted.
- Status is `planned`, `ready`, `active`, `completed`, `integrated`, or `blocked`.
- Dependencies point from prerequisite to successor.
- Only incomplete prerequisite edges contribute to readiness. `completed` and `integrated` predecessors are removed.
- Collisions describe overlap or merge risk and do not change indegrees.
- Use one branch and worktree per lane by default. Use a task-specific branch only for independently dispatched work.
- Optional modules may group multiple mergeable outputs inside a large lane. When modules exist, every task references a module in the same lane.
- Derive lane and optional module graphs from task dependencies; do not duplicate edges.
- Omit unresolved integration order and ask the human instead.
