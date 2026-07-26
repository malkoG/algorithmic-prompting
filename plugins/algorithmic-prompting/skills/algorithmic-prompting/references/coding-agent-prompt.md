# Coding-agent prompt

Create one standalone draft prompt per atomic commit unit. Keep broad lanes for parallel ownership, but give each planned commit its own bounded task prompt. Omit empty sections rather than inventing details.

```text
Implement <TASK_ID>: <OUTCOME>

Lane
- ID: <API | WEB | SDK | repository-specific lane>
- Contract: <required input> → <mergeable output>
- Owns: <paths or components; predictions unless declared an allowlist>
- Validation profile: <lane-level checks>

Work package
- Coordination ID: <API-01>
- Commit intent: <human-readable outcome without the coordination ID>
- Checklist: <inseparable implementation and tests for this one commit>

Outcome
<One concrete, verifiable outcome.>

Context
<Only the repository, product, and design context needed for this commit unit.>

Execution
<Use one or two short natural-language sentences. State what this commit unit waits for, or where it starts and which assigned lane branch it uses. When branch creation is authorized, include the exact base SHA and exact child branch. State that the coordinator will integrate the returned commit.>

Branch setup
- Inspect the current branch and `HEAD` before editing.
- If already on the assigned child branch, use it and do not create another branch.
- If detached at the exact base SHA and branch creation is authorized, create only the assigned child branch.
- If the current branch, `HEAD`, assigned branch, or authorization does not match, stop and report the mismatch.
- Do not check out or advance the parent integration branch from this worktree.

Scope
- <One atomic, reviewable, and revertible behavior change>
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
After successful validation, end this dispatched task with exactly one focused commit. Keep this prompt and commit one-to-one: do not combine it with another task or split it across commits. Use a human-readable imperative subject, a blank line, and two to four `-` bullet lines describing meaningful changes and validation. Do not mention internal coordination identifiers such as `API-01`, module IDs, the branch name, or the worktree in the commit message. Derive the message from the actual diff and planned commit intent.

Return the child branch, commit SHA, concise summary of changes, files touched, validations run and their results, assumptions, and remaining risks. Do not merge, rebase, push, or delete the worktree or branch. Stop without creating a success commit if a prerequisite is unavailable, required validation fails, the requested scope materially expands, or a collision makes the task unsafe to continue.

Make the child branch and full commit SHA explicit so the coordinator can report `Merge: <child branch> @ <full commit SHA> → <target branch>`. A worktree name or path is diagnostic context, not a merge identity.
```

## Prompt rules

- Write in imperative language and make the outcome testable.
- Keep the prompt bounded to one atomic commit unit inside one broad lane.
- Make the lane contract, ownership, output, and validation explicit.
- Keep inseparable implementation and focused tests in one prompt. Split only when the next change is independently meaningful and revertible.
- When modules are present, state the module compactly, but do not introduce modules in ordinary lane-level plans.
- Include lane-level validation and add task-specific checks rather than replacing either one.
- Include enough context to avoid forcing the coding agent to rediscover the dependency plan.
- Distinguish predicted files from a strict file allowlist.
- Mention every hard predecessor and every known collision relevant to the task.
- Do not claim a task is ready merely because its draft prompt exists.
- Write execution metadata as one or two short natural-language sentences, not a form. Omit default strategy language. Mention prerequisites only when blocked, and mention stacking or an unresolved integration choice only when it changes execution.
- Keep planning-time prompts non-mutating. Add branch-creation and commit authorization only after the human approves dispatch.
- Require one commit per task prompt. Never combine two task nodes into one commit or split one task across several commits.
- Keep internal graph identifiers out of commit messages. Use an outcome-based subject followed by two to four bullet lines; natural technical terms such as API or SDK are allowed when they describe the change rather than a coordination label.
- Allocate a lane child as `task/<goal-slug>/<lane-id-lower>`. Add a task suffix only for an intentionally separate task worktree. Never create `<base-branch>/<lane>` when `<base-branch>` already exists.
- Include an exact base SHA whenever branch creation is authorized. Do not allow the worker to choose a substitute base or alternate branch name.
- Do not embed approval to create worktrees, merge, rebase, push, delete branches, or modify sibling work.
- Replace planning-time unknowns after the human selects a Kahn batch; retain visible unresolved decisions if the human has not answered them.

## Dispatch example

For parent branch `feature/authentication` at `abc123`, assign the `API` lane a child such as `task/authentication/api`, not `feature/authentication/api`.

```text
Execution

Start this API commit unit from `feature/authentication` at `abc123` on `task/authentication/api` in the managed worktree. Complete only its bounded work package and return one focused commit.

Run the API validation profile.

- You are authorized to create exactly the assigned child branch if this managed worktree is detached at abc123.
- If already on task/authentication/api, continue without creating another branch.
- Otherwise, stop and report the mismatch.

After lane validation, create exactly one focused commit. Do not include `API-01` or another coordination identifier in its message. Use an outcome-based subject, a blank line, and two to four bullet lines describing the implementation and validation. Do not merge, rebase, push, or modify feature/authentication. Return the commit SHA and validation results to the parent coordinator.
```
