# Coding-agent prompt

Create one standalone draft prompt per task. Use this structure, omitting empty sections rather than inventing details.

```text
Implement <TASK_ID>: <TITLE>

Lane
- ID: <API | WEB | SDK | repository-specific lane>
- Scope: <lane responsibility>
- Likely paths/components: <lane predictions, not an allowlist>
- Validation profile: <lane-level checks>

Module
- ID: <API-AUTH | repository-specific module>
- Contract: <required input> → <mergeable output>
- Owns: <exclusive paths or components>
- Local tasks: <API-01 → API-02 | task IDs>

Outcome
<One concrete, verifiable outcome.>

Context
<Only the repository, product, and design context needed for this task.>

Execution
<Use one or two short natural-language sentences. State what this task waits for, or where it starts and which assigned branch it uses. When branch creation is authorized, include the exact base SHA and exact child branch. State that the coordinator will merge the returned commit.>

Branch setup
- Inspect the current branch and `HEAD` before editing.
- If already on the assigned child branch, use it and do not create another branch.
- If detached at the exact base SHA and branch creation is authorized, create only the assigned child branch.
- If the current branch, `HEAD`, assigned branch, or authorization does not match, stop and report the mismatch.
- Do not check out or advance the parent integration branch from this worktree.

Scope
- <Required behavior or implementation step>
- Likely files: <paths or patterns; guidance unless explicitly declared an allowlist>

Out of scope
- <Sibling behavior this agent must not absorb>
- Do not perform unrelated refactors or cleanup.

Coordination risks
- <Same-file collision, central registry, migration, generated artifact, or sibling ownership>
- <Expected integration order, or say that it needs human resolution>

Acceptance criteria
- <Observable criterion>

Validation
- <Test, lint, typecheck, build, or focused manual check>

Handoff
Create the requested focused commit only when commit authorization is present. Return the child branch, commit SHA, concise summary of changes, files touched, validations run and their results, assumptions, and remaining risks. Do not merge, rebase, push, or delete the worktree or branch. Stop and report if a prerequisite is unavailable, the requested scope materially expands, or a collision makes the task unsafe to continue.

Make the child branch and full commit SHA explicit so the coordinator can report `Merge: <child branch> @ <full commit SHA> → <target branch>`. A worktree name or path is diagnostic context, not a merge identity.
```

## Prompt rules

- Write in imperative language and make the outcome testable.
- Keep the prompt bounded to one subtask even when the parent goal is broader.
- State the lane explicitly, but never infer readiness from lane membership.
- When modules are present, state the module contract and ownership compactly. The module is the default branch, worktree, validation, and merge unit; the task remains the coding scope.
- Include lane-level validation and add task-specific checks rather than replacing either one.
- Include enough context to avoid forcing the coding agent to rediscover the dependency plan.
- Distinguish predicted files from a strict file allowlist.
- Mention every hard predecessor and every known collision relevant to the task.
- Do not claim a task is ready merely because its draft prompt exists.
- Write execution metadata as one or two short natural-language sentences, not a form. Omit default strategy language. Mention prerequisites only when blocked, and mention stacking or an unresolved integration choice only when it changes execution.
- Keep planning-time prompts non-mutating. Add branch-creation and commit authorization only after the human approves dispatch.
- Allocate a module child as `task/<goal-slug>/<module-id-lower>`. For a task-only plan, use `task/<goal-slug>/<task-id-lower>-<task-slug>`. Never create `<base-branch>/<task>` when `<base-branch>` already exists.
- Include an exact base SHA whenever branch creation is authorized. Do not allow the worker to choose a substitute base or alternate branch name.
- Do not embed approval to create worktrees, merge, rebase, push, delete branches, or modify sibling work.
- Replace planning-time unknowns after the human selects a Kahn batch; retain visible unresolved decisions if the human has not answered them.

## Dispatch example

For parent branch `feature/authentication` at `abc123`, assign module `API-AUTH` a child such as `task/authentication/api-auth`, not `feature/authentication/api-auth`.

```text
Execution

Start API-AUTH from `feature/authentication` at `abc123` on `task/authentication/api-auth` in the managed worktree. Implement only API-01 in this task prompt and return one commit for the module branch.

Run the API validation profile.

- You are authorized to create exactly the assigned child branch if this managed worktree is detached at abc123.
- If already on task/authentication/api-auth, continue without creating another branch.
- Otherwise, stop and report the mismatch.

After lane-level and task-specific validation, create exactly one focused commit for API-01. Do not merge, rebase, push, or modify feature/authentication. Return the commit SHA and validation results to the parent coordinator.
```
