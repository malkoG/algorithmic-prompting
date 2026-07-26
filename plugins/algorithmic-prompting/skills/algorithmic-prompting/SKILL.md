---
name: algorithmic-prompting
description: Partition software work into architecture lanes such as API, WEB, and SDK; decompose each lane into dependency-aware subtasks; generate a draft coding-agent prompt for every subtask; present large plans through clickable temporary task files with kebab-case names; distinguish hard prerequisites from same-file merge risks; render the resulting DAG; and coordinate human-in-the-loop execution with Kahn's algorithm across Git worktrees. Use for implementation plans, tech specs, ADRs, issue breakdowns, coding-agent delegation, parallel agent work, worktree scheduling, merge-order planning, lane-aware planning, large task graphs, or dependency-graph reviews.
---

# Algorithmic Prompting

Turn a goal into a reviewable DAG and advance it only through explicit human decisions. Treat the graph as an execution control surface, not merely a diagram.

## Build the plan

1. Inspect the request, relevant tech specs or ADRs, repository guidance, and affected code. Do not require a formal design document.
2. Identify architectural lanes from the request and repository, preserving user-provided names such as `API`, `WEB`, and `SDK`. Use `CORE` when only one lane is meaningful.
3. Split work inside each lane into the smallest independently verifiable subtasks that still produce meaningful progress. Give each a stable lane-aware ID such as `API-01`, `WEB-01`, or `SDK-01`.
4. For every subtask, record its lane, outcome, likely files or file patterns, lane validation profile, completion gate, and a standalone draft coding-agent prompt.
5. Classify relationships:
   - Add a hard directed edge `A -> B` only when B needs A's result before it can satisfy its completion gate.
   - Record a file collision when tasks may touch the same file or tightly coupled generated artifact.
   - Do not turn file overlap alone into a hard edge. Infer an integration order when justified; otherwise flag it for human choice.
6. Exclude lane and synthetic goal nodes from dependency calculations. With no hard edges between subtasks, describe the subtask graph as a forest of independent nodes; if the goal node is shown, describe that view as a star.
7. Check for cycles before scheduling. If a cycle exists, stop Kahn processing, show the cycle, and propose ways to split a task or relax an incorrect edge. Never silently remove an edge.

Use `references/plan-schema.md` when persisting a machine-readable plan. Run `scripts/graph_ready.py <plan.json>` to validate it and calculate the current ready queue.

## Model architectural lanes

- Treat a lane as task metadata and a visual partition, not as a prerequisite node.
- Use short uppercase lane IDs containing letters or digits. Number tasks independently within each lane as `<LANE>-<NN>`.
- Record each lane's scope, likely paths or components, and validation profile. Treat paths as predictions unless the human declares an allowlist.
- Prefer repository-native boundaries and terminology over a fixed global taxonomy.
- Keep cross-lane dependencies explicit. Same lane does not imply dependency; different lanes do not imply independence.
- Render lanes as Mermaid subgraphs while preserving one global hard-dependency DAG.
- When ranking otherwise equivalent ready tasks, prefer a batch spread across lanes, but let hard dependencies and collision evidence override lane diversity.

## Draft a coding-agent prompt for every task

Generate prompts for all subtasks during planning, including tasks that are not ready yet. Make each prompt independently understandable and easy for the human to edit before dispatch. Follow `references/coding-agent-prompt.md`.

Each prompt must include:

- The stable lane-aware task ID, lane, title, and concrete outcome.
- Relevant repository and product context without copying the entire parent request.
- The prerequisite gate and whether the task is currently ready. For a blocked task, say exactly what must become available before it starts.
- The base branch, exact base SHA, assigned child branch, and worktree when known; otherwise say that the coordinator will assign them.
- In-scope behavior and likely files. Treat inferred file paths as guidance, not an exclusive allowlist.
- Explicit exclusions that keep the agent from absorbing sibling tasks.
- Collision risks, active sibling ownership, and intended integration order when known.
- Acceptance criteria and the lane-specific validation profile plus proportionate task checks.
- A handoff contract requiring a concise summary of changes, files touched, tests run, results, assumptions, and remaining risks.

Keep workspace metadata in one compact `Dispatch` block. Combine readiness with any blocking prerequisites, combine the base branch with the exact base SHA, and use short `Branch`, `Worktree`, and `Branch creation` fields. Omit the default shared-base strategy; mention stacking or an unresolved integration choice only when it changes execution.

Tell the coding agent to work only on the assigned subtask, preserve unrelated user changes, follow repository instructions, and stop to report a missing prerequisite or materially expanded scope. A planning-time draft must not authorize branch creation. After HITL approves dispatch, the final prompt may authorize creation of exactly one assigned child branch from an exact base SHA; it must not authorize any alternate branch, merging, pushing, or unrelated cleanup. Never hide unresolved HITL choices inside a prompt; label them for the human before dispatch.

## Use clickable task files for large plans

When a plan has more than five subtasks, or when the user asks for compact or clickable navigation, keep detailed task content out of chat while making the conversation itself sufficient for routine navigation:

1. Persist the plan JSON in a temporary directory outside the repository unless the user requests a durable project location.
2. Run `scripts/render_task_files.py <plan.json> [--output-dir <existing-temp-dir>]`.
3. Paste the renderer's `conversation_summary` into chat, including its Mermaid topology. Treat it as the primary plan view and `00-task-index.md` as an optional deep dive.
4. For 12 or fewer tasks, list every task in the conversation as one compact linked line containing its ID, title, and status. For larger plans, show total status counts, per-lane ready/total counts, and direct links for ready, active, and blocked tasks; summarize waiting and completed tasks by count.
5. Always show the lane-grouped Mermaid graph, material collision warnings, and the smallest next HITL decision directly in chat. Include every task node and hard dependency edge; render collision risks as dashed links labeled `collision`. For more than 12 tasks, use task IDs alone as node labels to keep the graph compact. Do not require an index click to understand topology, learn what can run next, or see what needs human input. Do not inline every coding-agent prompt.
6. Reuse the same output directory when the graph changes. The renderer preserves the first filename assigned to each stable task ID so existing links do not move.
7. Do not automatically delete task files. Let system temporary storage expire, or ask before removing a user-selected durable directory.

Name user-facing files `<task-id-lower>-<task-summary-kebab>.md`, for example `api-01-add-authentication-endpoint.md`. Use lowercase ASCII kebab case, collapse repeated hyphens, remove punctuation, and limit the summary slug to 60 characters. Keep the canonical uppercase ID in the document heading. Name the navigator `00-task-index.md`.

## Apply Kahn's algorithm with HITL gates

Calculate indegrees from incomplete hard-prerequisite edges only. A task is ready when its indegree is zero and its status is `planned` or `ready`.

At each iteration:

1. Present the zero-indegree ready queue globally and grouped by lane.
2. Show collision warnings among ready tasks and with active tasks.
3. Propose one or more parallel batches. Prefer lane diversity among equally safe tasks, keep hard-dependent tasks in different iterations, and label same-file merge risks with a proposed integration order.
4. Ask the human to select or approve the next batch and resolve any ambiguous ordering. Do not create worktrees, delegate implementation, merge, or mark work complete without authorization covering that action.
5. For an approved batch, refresh each selected draft prompt with the approved base branch and SHA, child branch, branch-creation mode, worktree, current prerequisite state, sibling ownership, validation commands, and integration gate. Present the final prompts for human approval before dispatch.
6. After implementation, verify each task's completion gate. Ask for or record human acceptance, then mark the task `completed` or `integrated` as appropriate.
7. Remove only accepted prerequisite nodes from the working graph, decrement successor indegrees, and present the newly unlocked queue.
8. Continue until all tasks are accepted or no node is ready. If unfinished nodes remain with no ready node, report a cycle, rejected completion gate, or external blocker.

A hard-dependent successor becomes eligible only when the predecessor's output is available to it. Normally this means the predecessor is integrated into the shared base. A stacked branch based on the predecessor may also satisfy the gate when the human explicitly chooses that strategy.

## Worktree scheduling rules

- Assign one coherent subtask or tightly coupled task chain per worktree.
- Prefer independent zero-indegree tasks for parallel worktrees.
- Name child branches in a namespace separate from the parent branch as `task/<goal-slug>/<task-id-lower>-<task-slug>`, for example `task/authentication/api-01-add-endpoint`. If `feature/authentication` exists, never propose `feature/authentication/api-01`; Git cannot use an existing branch ref as a directory prefix.
- Let the coordinator allocate and validate every branch name. If worker-managed creation is approved, authorize the worker to create only that exact branch from the recorded base SHA.
- In a detached managed worktree, create the assigned branch only when `HEAD` equals the recorded base SHA. If the worktree is already on the assigned branch, continue without recreating it. For any other branch or SHA, stop and report the mismatch.
- Never assume separate worktrees eliminate merge conflicts; they isolate working copies, not integration risk.
- Keep branch ownership, base commit, and intended merge order explicit.
- Re-evaluate predicted file sets after implementation begins. Add newly discovered collisions without rewriting historical decisions.
- Treat generated files, schemas, lockfiles, migrations, and central registries as high-risk collision surfaces even when paths differ.
- Suggest commands but execute repository mutations only when the user asks for implementation or worktree setup.

## Required output

Provide the following compact sections:

1. **Lane map** — lane ID, scope, likely paths or components, and validation profile.
2. **Task inventory** — lane-aware ID, outcome, likely files, validation, and status.
3. **Hard dependencies** — directed edges with one-sentence reasons.
4. **Collision constraints** — task pairs, overlapping surface, risk, and proposed merge order if known.
5. **Topology** — a Mermaid DAG grouped into lane subgraphs; render collisions as dashed, clearly labeled links.
6. **Kahn state** — completed nodes, current indegrees, global and per-lane ready queues, and proposed parallel batches.
7. **Draft coding-agent prompts** — one clearly labeled, copy-ready prompt per stable task ID.
8. **Human decision** — the smallest explicit choice needed to advance the graph.

State assumptions and confidence when file ownership or prerequisites are inferred. Keep the graph editable: incorporate human corrections, recompute indegrees, and preserve stable task IDs.

In clickable task-file mode, put the full required output in the index and task files. In chat, lead with the paste-ready brief summary: plan status, lane counts, compact direct task links, and the lane-grouped Mermaid topology according to the size rules above. Then show material warnings and the next human decision. Keep the index as an optional final link, never the required starting point.
