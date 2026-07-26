---
name: algorithmic-prompting
description: Turn a software goal into a dependency-aware plan with parallel work lanes, atomic commit units, an immediate clickable task index, asynchronously landed coding-agent prompts, and human-approved integration guidance. Use for implementation planning, specs, ADRs, issue breakdowns, parallel agent work, worktree coordination, or merge sequencing.
---

# Algorithmic Prompting

Turn a goal into work that coding agents can execute and a human can control.

## Mental model

```text
Goal
└── Lanes — work that can proceed independently
    └── Commit units — one task, one prompt, one commit

Dependencies determine what is ready next.
```

Derive lane names from the project. Do not impose a fixed technology or product taxonomy.

## Build the plan

1. Inspect the request, repository guidance, relevant design documents, and only enough affected-code entry points to locate ownership boundaries.
2. Choose the fewest broad lanes that expose safe parallel work. Give each lane a clear input, ownership boundary, validation profile, and mergeable output.
3. Split each lane into the fewest atomic commit units that make the history understandable and revertible, usually one to three.
4. Give every unit a stable `<LANE>-<NN>` coordination ID and a human-readable commit intent.
5. Add a hard edge only when the successor cannot pass its completion gate without the predecessor.
6. Record likely file overlap as a collision, not automatically as a dependency.
7. Reject cycles. If a collapsed lane graph cycles, merge coupled lanes or isolate a small shared prerequisite.

Keep this scan compact. Record a short `prompt_seed` for each task rather than producing its complete prompt during the scan.

## Choose prompt depth

Use `lean` unless the human asks otherwise. `balanced` adds task-local context for ambiguous work; `thorough` is for high-risk work such as security, migrations, and compatibility changes. A task may override the plan default.

Follow [references/prompt-profiles.md](references/prompt-profiles.md). Detail agents return only a compact task delta; the renderer adds the shared execution contract.

Keep implementation and focused tests in the same commit unit. Do not create separate nodes for routine steps, individual files, formatting, or generated output unless they are independently valuable.

Use [references/plan-schema.md](references/plan-schema.md) for the persisted plan. Run `scripts/graph_ready.py <plan.json>` to validate it and calculate ready lanes and tasks.

## Publish the index immediately

Persist the compact plan outside the repository unless the human requests a durable location. Create stable filenames, the index, and placeholder task files before starting detail work:

```text
scripts/render_task_files.py <plan.json> --placeholders [--output-dir <existing-directory>]
```

This must create `00-task-index.md`, `.task-files.json`, and one lightweight task file per stable kebab-case filename. Paste the compact conversation summary and index link before dispatching detail jobs.

## Let complete prompts land independently

Follow [references/detail-agent-contract.md](references/detail-agent-contract.md). Use subagents for the independent prompt-detail tasks. Dispatch them concurrently and return immediately after dispatch.

1. Spawn one subagent per prompt-detail task after all placeholders exist. Each subagent owns only its assigned detail result and task file.
2. Give each job the shared plan path, output directory, its task ID, prompt profile, lane contract, repository guidance, hard prerequisites, collision hints, and likely paths. Prefer bounded task-local context over full conversation history.
3. Keep detail work read-only with respect to the repository. Do not implement code, create branches or worktrees, or commit changes.
4. Have each job write one structured detail result to a unique temporary path, then run:

```text
scripts/land_task_detail.py <plan.json> <detail.json> --output-dir <task-directory>
```

5. Let the landing script atomically replace only that task's placeholder and persist its detail result. Detail jobs must never edit `00-task-index.md`, `.task-files.json`, another task file, or the shared plan.
6. Dispatch all prompt-detail subagents concurrently. After every dispatch is accepted, return immediately. Do not wait for their messages or perform a fan-in.
7. If subagents cannot continue after return, keep the placeholders and report that asynchronous dispatch is unavailable. Do not silently turn the request into a blocking workflow.

Prompt-detail jobs may run concurrently even when implementation tasks have hard dependencies. Their prompts describe those dependencies; they do not execute the work. Newly discovered graph proposals and uncertainties stay in the landed task file for later human integration.

Reuse the same output directory when the plan changes. Placeholder rendering must not overwrite task files that have already landed.

## Advance work with human approval

Use incomplete hard prerequisites to calculate the ready queue.

1. Show ready lanes and ready commit units.
2. Show material collisions and propose the widest safe parallel batch.
3. Ask the human to approve the batch in natural language.
4. After approval, finalize the selected prompt's branch assignment.
5. After each accepted commit, recompute the graph and show newly ready work.
6. Stop on a cycle, failed completion gate, unresolved collision, or external blocker.

Keep coordination concise:

```text
Start: <task IDs> from <base branch>
Merge: <child branch> @ <full commit SHA> → <target branch>
Next: <newly ready task IDs | none>
```

The branch and full SHA identify work for integration. A worktree name or path does not.

## Prepare coding-agent prompts

Create one complete prompt per commit unit through its detail job and landing script. [references/coding-agent-prompt.md](references/coding-agent-prompt.md) is the source contract for the compiled prompt. In `lean`, keep the task file focused on the compiled prompt instead of duplicating its sections around it.

Each prompt must state:

- Task ID, lane, commit intent, and outcome
- Prerequisites and readiness
- Scope, likely files, exclusions, and collision risks
- Acceptance criteria and validation
- Approved base, child branch, and worktree when known
- Commit and handoff requirements

Planning drafts do not authorize branch creation or repository mutations. After human approval, authorize only the exact child branch from the recorded base SHA. Do not authorize merging, pushing, cleanup, or sibling work.

## Commit and handoff

A successful task produces exactly one focused commit. Do not combine task nodes or split one task across commits.

The commit message uses:

- An outcome-based imperative subject
- A blank line
- Two to four bullet lines describing meaningful changes and validation
- No coordination IDs, branch names, or worktree names

If validation fails or scope expands materially, stop without creating a success commit.

Return the child branch, full commit SHA, changed files, validation results, assumptions, and remaining risks.

## Worktree rules

- Use one worktree and child branch per lane by default.
- Run a lane's dependent commit units as an ordered series on that branch.
- Give independently dispatched tasks separate branches or worktrees; never let concurrent agents write the same branch.
- Preserve unrelated changes and follow repository instructions.
- Re-evaluate collisions when actual changed files differ from predictions.
- Do not create, merge, rebase, push, or delete worktrees or branches without matching human authorization.

## Conversation output

Show:

1. Plan status and lane summary
2. Direct task links
3. Mermaid dependency topology
4. Material collision warnings
5. The smallest decision needed to continue
6. The `00-task-index.md` link

Keep detailed prompts in task files. The conversation must still reveal what is ready and what happens next.
For fire-and-forget planning, also state that prompt files are landing asynchronously and that an unchanged placeholder means its detail job is still running or failed.
