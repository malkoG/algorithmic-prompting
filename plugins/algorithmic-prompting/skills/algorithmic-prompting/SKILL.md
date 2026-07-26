---
name: algorithmic-prompting
description: Partition software work into broad parallel execution lanes, split each lane into atomic commit-sized subtasks, always create a clickable temporary task index and task files, derive lane and commit dependency DAGs, generate bounded coding-agent prompts, and coordinate human-in-the-loop Kahn scheduling across Git worktrees. Use for implementation plans, tech specs, ADRs, issue breakdowns, coding-agent delegation, parallel agent work, commit-wise planning, worktree scheduling, merge-order planning, or dependency-graph reviews.
---

# Algorithmic Prompting

Turn a goal into a reviewable DAG and advance it only through explicit human decisions. Treat the graph as an execution control surface, not merely a diagram.

## Build the plan

1. Inspect the request, relevant tech specs or ADRs, repository guidance, and affected code. Do not require a formal design document.
2. Identify the fewest broad execution lanes that expose meaningful parallelism, usually two to six. Preserve useful names such as `API`, `WEB`, and `SDK`; use repository-specific capability names when they create cleaner ownership.
3. Give every lane a clear input, exclusive or low-collision ownership, independent validation, and one mergeable output. Prefer lanes that can start from the same base and finish without waiting for sibling implementation details.
4. Split each lane into the fewest atomic commit units that make the history reviewable and revertible, usually one to three. Create a separate task for an independently meaningful behavior, prerequisite, owner handoff, merge or rollback boundary, or validation gate. Do not split merely because several files or routine steps exist.
5. Map every retained task one-to-one to a planned commit and record a human-readable `commit_intent` without the task ID. Use an optional module only when one lane truly contains multiple independently mergeable outputs. Give every task a stable lane-aware ID such as `API-01`, `WEB-01`, or `SDK-01`.
6. Classify relationships:
   - Add a hard directed edge `A -> B` only when B needs A's result before it can satisfy its completion gate.
   - Record a file collision when tasks may touch the same file or tightly coupled generated artifact.
   - Do not turn file overlap alone into a hard edge. Infer an integration order when justified; otherwise flag it for human choice.
7. Derive the lane DAG by collapsing cross-lane task edges. If modules exist, derive their DAG the same way. Do not maintain duplicate edge sources. With no hard edges, describe the lanes as a forest of independent nodes; if the goal node is shown, describe that view as a star.
8. Check task, lane, and optional module graphs for cycles. A lane-level cycle means the partition is too coupled: merge lanes or extract a small bridge contract. Never silently remove an edge.

Use `references/plan-schema.md` when persisting a machine-readable plan. Run `scripts/graph_ready.py <plan.json>` to validate it and calculate the current ready queue.

## Model parallel execution lanes

- Treat a lane as the default branch, worktree, validation, and merge unit. Its DAG edges are derived from task prerequisites.
- Use short uppercase lane IDs containing letters or digits. Number tasks independently within each lane as `<LANE>-<NN>`.
- Record each lane's scope, likely paths or components, and validation profile. Treat paths as predictions unless the human declares an allowlist.
- Prefer repository-native boundaries and terminology over a fixed global taxonomy.
- Keep cross-lane dependencies sparse and explicit. If nearly every lane waits for another, reconsider the boundaries instead of accepting poor parallelism.
- Optimize for a wide first Kahn frontier: maximize lanes that can safely start from the shared base without inventing weak boundaries.
- Distinguish an implementation dependency from an integration dependency. If a stable contract, fixture, mock, or stub lets a consumer lane work safely, do not block it on the producer's implementation.
- When several lanes can implement against one contract but need joint verification, let them run in parallel and add one narrow `INT` integration lane after them instead of chaining the lanes together.
- Keep shared contracts small and early. Move generated files, migrations, lockfiles, and central registries into one owning lane or a narrow bridge lane.
- Render the collapsed lane DAG as the primary Mermaid view. Show local task topology only when a lane was intentionally split.

## Keep the hierarchy shallow

- Prefer `goal → lanes → commit units`. Keep most lanes to one to three commit units; use one when the lane is already atomic.
- Split only when the resulting commits are independently understandable and revertible. Keep inseparable implementation and its focused tests in the same commit.
- Do not create a node for routine implementation steps, individual files, test files, or expected refactors that the same agent can complete safely in one worktree.
- Do not create standalone commits for scaffolding, formatting, generated output, or tests unless they are independently valuable changes.
- Use modules only as an escape hatch for a genuinely large lane. Never add modules merely to make the graph look more structured.
- If two proposed lanes share a hotspot or require constant coordination, merge them. If one small contract unlocks many lanes, isolate that contract and keep the downstream lanes broad.

Use this compact lane card in conversation and prompts. Omit an inapplicable `Merge` or `Next` line.

```text
Lane: API
Input: approved auth contract
Owns: api/auth/**
Commits: verify credentials → issue sessions
Output: authenticated endpoint
Merge: task/authentication/api @ <full commit SHA> → feature/authentication
Next: SDK, WEB
```

## Draft one coding-agent prompt per commit unit

Generate one prompt per planned commit unit, including tasks that are not ready yet. A lane that needs one commit gets one prompt; a lane with two or three meaningful commits gets one prompt for each. Make each prompt independently understandable and easy for the human to edit before dispatch. Follow `references/coding-agent-prompt.md`.

Each prompt must include:

- The stable lane-aware task ID, lane, title, and concrete outcome.
- A human-readable commit intent that does not contain the task ID.
- Its lane input-to-output contract, exclusive ownership, and compact internal checklist. Mention a module only when one actually exists.
- Relevant repository and product context without copying the entire parent request.
- The prerequisite gate and whether the task is currently ready. For a blocked task, say exactly what must become available before it starts.
- The base branch, exact base SHA, assigned child branch, and worktree when known; otherwise say that the coordinator will assign them.
- In-scope behavior and likely files. Treat inferred file paths as guidance, not an exclusive allowlist.
- Explicit exclusions that keep the agent from absorbing sibling tasks.
- Collision risks, active sibling ownership, and intended integration order when known.
- Acceptance criteria and the lane-specific validation profile plus proportionate task checks.
- A handoff contract requiring a concise summary of changes, files touched, tests run, results, assumptions, and remaining risks.

Express workspace metadata as one or two short natural-language sentences under `Execution`; never ask the human to fill a dispatch form. Derive the sentences from the human's coordination decision. Include blocking task IDs only when waiting. When branch creation is authorized, name the exact base branch and SHA and the exact child branch. Say where the coordinator will merge the returned commit. Omit default strategy language; mention stacking or an unresolved integration choice only when it changes execution.

Keep human-facing Kahn coordination to these compact lines when applicable:

```text
Start: <task IDs> from <base branch>
Merge: <child branch> @ <full commit SHA> → <target branch>
Next: <newly ready task IDs | none>
```

Use the child branch plus exact commit SHA as the merge identity. The branch is recognizable; the SHA pins the reviewed result. Never use a worktree name or path as the merge target. Omit any line that is not yet applicable and avoid explanatory prose unless a collision, stack, or ambiguity needs a decision.

Tell the coding agent to work only on the assigned subtask, preserve unrelated user changes, follow repository instructions, and stop to report a missing prerequisite or materially expanded scope. A planning-time draft must not authorize branch creation. After HITL approves dispatch, the final prompt may authorize creation of exactly one assigned child branch from an exact base SHA; it must not authorize any alternate branch, merging, pushing, or unrelated cleanup. Never hide unresolved HITL choices inside a prompt; label them for the human before dispatch.

## End every dispatched task with a commit

- Require exactly one focused commit after each dispatched task passes validation. The task graph and successful commit series must have a one-to-one mapping.
- Treat graph IDs such as `API-01`, `WEB-02`, and module IDs as coordination metadata. Never include them as labels in the commit subject, body, or trailers. Natural product and architecture terms remain fine.
- Write a human-readable imperative subject describing the outcome, then a blank line and two to four `-` bullet lines describing meaningful changes and validation.
- Derive the message from the actual diff. Do not use generic subjects such as `Complete task`, repeat the branch name, or mention the worktree.
- If the task is blocked or required validation fails, stop and report instead of creating a success commit.

Use this shape:

```text
Add authenticated session handling

- Validate credentials and issue session tokens
- Preserve existing error responses for rejected requests
- Cover successful and rejected sign-in flows
```

## Create clickable task files for every plan

Use the same task-file experience for every plan, including a single task. Keep detailed prompt content in files while making the conversation sufficient for routine navigation:

1. Persist every plan JSON in a temporary directory outside the repository unless the user requests a durable project location.
2. Always run `scripts/render_task_files.py <plan.json> [--output-dir <existing-temp-dir>]`. Never skip rendering because the task count is small.
3. Paste the renderer's `conversation_summary` into chat, including its Mermaid topology. Treat it as the primary plan view and `00-task-index.md` as an optional deep dive.
4. For 12 or fewer tasks, list every task in the conversation as one compact linked line containing its ID, title, and status. For larger plans, show total status counts, per-lane ready/total counts, and direct links for ready, active, and blocked tasks; summarize waiting and completed tasks by count.
5. Always show the compact lane cards, collapsed lane Mermaid graph, material collision warnings, and smallest next HITL decision directly in chat. Show task topology only for intentionally split lanes. Do not require an index click to understand what can run next or what needs human input. Do not inline every coding-agent prompt.
6. Reuse the same output directory when the graph changes. The renderer preserves the first filename assigned to each stable task ID so existing links do not move.
7. Do not automatically delete task files. Let system temporary storage expire, or ask before removing a user-selected durable directory.

Every run must create `00-task-index.md`, one kebab-case Markdown file per task, and `.task-files.json`. Return the index link in conversation even for one task so navigation stays consistent across plans.

Name user-facing files `<task-id-lower>-<task-summary-kebab>.md`, for example `api-01-add-authentication-endpoint.md`. Use lowercase ASCII kebab case, collapse repeated hyphens, remove punctuation, and limit the summary slug to 60 characters. Keep the canonical uppercase ID in the document heading. Name the navigator `00-task-index.md`.

## Apply Kahn's algorithm with HITL gates

Calculate indegrees from incomplete hard-prerequisite edges only. A lane is globally ready when its collapsed lane indegree is zero and it contains ready work. A retained task is locally ready when its task indegree is zero and its status is `planned` or `ready`.

At each iteration:

1. Present the zero-indegree lane queue and the ready commit units inside each lane.
2. Show collision warnings among ready tasks and with active tasks.
3. Propose the widest safe parallel lane batch. Keep hard-dependent lanes in different iterations and label merge risks with a proposed integration order. Use the compact lane card plus `Start`, `Merge`, and `Next` lines instead of prose.
4. Ask the human to select or approve the next batch and resolve any ambiguous ordering. Accept a natural-language answer such as "Start API-01 and WEB-01 from main; merge API-01 first." Interpret it, then reflect the normalized start points and merge order concisely. Ask a follow-up only when branch, base, or ordering remains materially ambiguous. Do not require a structured response. Do not create worktrees, delegate implementation, merge, or mark work complete without authorization covering that action.
5. For an approved lane batch, allocate one child branch and worktree per lane. Refresh each selected commit-unit prompt with its approved base branch and SHA, lane child branch, branch-creation mode, worktree, prerequisite state, sibling ownership, validation commands, integration gate, commit intent, and the commit contract above. Present final prompts for human approval before dispatch.
6. After implementation, require the successful task's focused commit, verify its completion gate, and record the full commit SHA. Ask for or record human acceptance, then mark the task `completed` or `integrated` as appropriate. Show `Merge: <child branch> @ <full commit SHA> → <target branch>`; never substitute the worktree name.
7. Remove only accepted prerequisite nodes from the working graph, decrement successor indegrees, and present the newly unlocked queue as `Next: <task IDs>`.
8. Continue until all tasks are accepted or no node is ready. If unfinished nodes remain with no ready node, report a cycle, rejected completion gate, or external blocker.

A hard-dependent successor becomes eligible only when the predecessor's output is available to it. Normally this means the predecessor is integrated into the shared base. A stacked branch based on the predecessor may also satisfy the gate when the human explicitly chooses that strategy.

## Worktree scheduling rules

- Assign one broad, independently mergeable lane per worktree by default.
- Execute that lane's ready tasks as an ordered atomic commit series on the lane branch. End every dispatched task with exactly one focused commit; never squash separate task nodes into one implementation commit.
- When two tasks in one lane are genuinely independent and separately dispatched, give them separate branches or worktrees instead of letting concurrent agents write the same lane branch.
- Prefer independent zero-indegree tasks for parallel worktrees.
- Name lane branches in a namespace separate from the parent branch as `task/<goal-slug>/<lane-id-lower>`, for example `task/authentication/api`. Use a more specific task suffix only when a lane was intentionally split into separate worktrees. If `feature/authentication` exists, never propose `feature/authentication/api`; Git cannot use an existing branch ref as a directory prefix.
- Let the coordinator allocate and validate every branch name. If worker-managed creation is approved, authorize the worker to create only that exact branch from the recorded base SHA.
- In a detached managed worktree, create the assigned branch only when `HEAD` equals the recorded base SHA. If the worktree is already on the assigned branch, continue without recreating it. For any other branch or SHA, stop and report the mismatch.
- Never assume separate worktrees eliminate merge conflicts; they isolate working copies, not integration risk.
- Keep branch ownership, base commit, and intended merge order explicit.
- Re-evaluate predicted file sets after implementation begins. Add newly discovered collisions without rewriting historical decisions.
- Treat generated files, schemas, lockfiles, migrations, and central registries as high-risk collision surfaces even when paths differ.
- Suggest commands but execute repository mutations only when the user asks for implementation or worktree setup.

## Required output

Provide the following compact sections:

1. **Lane map** — lane ID, input, ownership, output, validation, branch, status, and downstream lanes.
2. **Commit-unit inventory** — task ID, lane, commit intent, outcome, validation, status, and the reason for every multi-commit split.
3. **Hard dependencies** — retained task edges and the derived cross-lane edges.
4. **Collision constraints** — lane or task pairs, overlapping surface, risk, and proposed merge order if known.
5. **Topology** — the collapsed lane Mermaid DAG, plus local task topology only where useful.
6. **Kahn state** — completed lanes, lane indegrees, global ready lanes, and proposed parallel batch.
7. **Draft coding-agent prompts** — one copy-ready prompt per planned commit unit.
8. **Human decision** — the smallest explicit choice needed to advance the graph.

State assumptions and confidence when file ownership or prerequisites are inferred. Keep the graph editable: incorporate human corrections, recompute indegrees, and preserve stable task IDs.

Always put the full required output in the index and task files. In chat, lead with the paste-ready brief summary: plan status, lane counts, compact direct task links, and the lane-grouped Mermaid topology according to the size rules above. Then show material warnings, the next human decision, and the `00-task-index.md` link. Keep the index optional for understanding the plan, but always create and expose it.
