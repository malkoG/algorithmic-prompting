# Coding-agent prompt

This is the source contract used by `scripts/land_task_detail.py` and the complete rendering mode of `scripts/render_task_files.py`. Create one complete prompt per atomic commit unit by combining shared plan fields with the task's concise guidance. Omit empty sections.

`lean` compresses this contract into short Guidance, Scope, Avoid, Done, Checks, and Execution sections. `balanced` and `thorough` retain the expanded structure below; their detail depth follows [prompt-profiles.md](prompt-profiles.md).

```text
Implement <TASK_ID>: <OUTCOME>

Lane
- Name: <project-derived lane>
- Contract: <required input> → <mergeable output>
- Ownership: <paths or components>
- Validation profile: <lane checks>

Commit unit
- Coordination ID: <LANE-NN>
- Commit intent: <human-readable outcome without the ID>
- Prerequisites: <task IDs or none>

Context
<Only the repository and design context needed for this unit.>

Task-specific guidance
<The task's prompt_seed. Do not repeat the shared contract here.>

Execution
<In one or two sentences, state what this unit waits for or the exact base, child branch, and managed worktree it uses. State where the coordinator will integrate the returned commit.>

Scope
- <One atomic behavior change>
- Likely files: <guidance unless declared an allowlist>

Out of scope
- <Sibling work>
- No unrelated refactors or cleanup.

Coordination risks
- <Known collision or shared ownership>
- <Integration order when known>

Acceptance criteria
- <Observable completion condition>

Validation
- <Focused checks>
- <Lane checks>

Branch safety
- Inspect the current branch and HEAD before editing.
- Continue when already on the assigned child branch.
- Create only the assigned branch when authorized and detached at the exact base SHA.
- Otherwise stop and report the mismatch.
- Do not advance the parent branch.

Commit and handoff
After successful validation, create exactly one focused commit for this unit. Do not combine it with another task or split it across commits.

Use an outcome-based imperative subject, a blank line, and two to four bullet lines describing meaningful changes and validation. Do not include coordination IDs, branch names, or worktree names.

Return the child branch, full commit SHA, changed files, validation results, assumptions, and remaining risks. Do not merge, rebase, push, or delete the branch or worktree. If a prerequisite is missing, validation fails, scope expands materially, or a collision makes the work unsafe, stop without creating a success commit.
```

## Rules

- Reason about shared project and execution facts once in `plan.json`; render them mechanically into every complete prompt.
- Keep only task-specific implementation judgment in `prompt_seed`.
- Keep the prompt bounded to one commit unit.
- Keep implementation and focused tests together.
- Distinguish predicted paths from an allowlist.
- Mention every hard predecessor and material collision.
- Do not infer readiness from lane membership.
- Keep planning drafts non-mutating.
- After approval, use `task/<goal-slug>/<lane-id-lower>` for the lane branch. Add a task suffix only when the task needs an independent worktree.
- Require an exact base SHA for worker-created branches.
- Use the child branch and full SHA—not a worktree path—as the integration identity.
