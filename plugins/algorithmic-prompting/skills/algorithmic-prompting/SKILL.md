---
name: algorithmic-prompting
description: Route a software goal through an intentionally structured repository layout into provisional parallel work lanes, publish an immediate task index, then use concurrent subagents for thorough task comprehension and independently landed coding-agent prompts. Use for implementation planning, specs, ADRs, issue breakdowns, parallel agent work, worktree coordination, or merge sequencing.
---

# Algorithmic Prompting

Turn a goal into work that coding agents can execute and a human can control.

## Mental model

```text
Goal
└── Layout-first routing — where to investigate
    └── Concurrent detail — how the system works
        └── Commit units — one task, one prompt, one commit

Dependencies determine what is ready next.
```

Derive lane names from the project. Do not impose a fixed technology or product taxonomy.

## Route before comprehending

Read [references/layout-first-routing.md](references/layout-first-routing.md) and the compact [references/plan-schema.md](references/plan-schema.md), then:

1. Read the request and repository instructions.
2. Run one file inventory. Use directory, module, package, map-document, schema-entity, workspace, and build-boundary names as routing evidence.
3. Choose the fewest broad ownership lanes. Create one `<LANE>-<NN>` task shell per independently investigated area by default.
4. Add only prerequisite edges stated by the request or explicit in the structured layout. Leave uncertain edges and collisions for detail subagents.
5. Persist a `routing` plan with `provisional` topology and validate it with `scripts/graph_ready.py <plan.json>`.

Before publishing the index, do not inspect implementation files, tests, SDK internals, UI internals, or complete design and schema documents. Do not determine exact files, validation, acceptance criteria, completion gates, branches, or prompt guidance. The coordinator routes investigation; it does not perform implementation comprehension.

Use `lean` unless the human names another profile. Do not read prompt-depth or coding-agent references during routing.

## Publish the index immediately

Persist the compact plan outside the repository unless the human requests a durable location. Create stable filenames, the index, and placeholder task files before starting detail work:

```text
scripts/render_task_files.py <plan.json> --placeholders [--output-dir <existing-directory>]
```

This must create `00-task-index.md`, `.task-files.json`, and one lightweight task file per stable kebab-case filename. Paste the compact conversation summary and index link before reading detail instructions or dispatching subagents.

## Let complete prompts land independently

Only after publishing the index, read [references/detail-agent-contract.md](references/detail-agent-contract.md). If a non-lean profile was requested, also read [references/prompt-profiles.md](references/prompt-profiles.md). Use subagents for the independent prompt-detail tasks. Dispatch them concurrently and return immediately after dispatch.

1. Spawn one subagent per prompt-detail task after all placeholders exist. Each subagent owns only its assigned detail result and task file.
2. Give each job the shared routing-plan path, output directory, its task ID, prompt profile, lane scope, repository guidance, visible layout evidence, and explicit prerequisites. Prefer bounded task-local context over full conversation history.
3. Have each subagent verify the provisional map against actual implementation and inspect deeply enough for thorough task comprehension. Keep detail work read-only with respect to the repository; do not implement code, create branches or worktrees, or commit changes.
4. Have each job write one structured detail result to a unique temporary path, then run:

```text
scripts/land_task_detail.py <plan.json> <detail.json> --output-dir <task-directory>
```

5. Let the landing script atomically replace only that task's placeholder and persist its detail result. Detail jobs must never edit `00-task-index.md`, `.task-files.json`, another task file, or the shared plan.
6. Dispatch all prompt-detail subagents concurrently. After every dispatch is accepted, return immediately. Do not wait for their messages or perform a fan-in.
7. If subagents cannot continue after return, keep the placeholders and report that asynchronous dispatch is unavailable. Do not silently turn the request into a blocking workflow.

Prompt-detail jobs may run concurrently even when implementation tasks have hard dependencies. Their prompts describe those dependencies; they do not execute the work. Detail subagents determine exact scope, likely files, validation, acceptance criteria, risks, and prompt guidance. Newly discovered graph proposals and uncertainties stay in the landed task file for later human integration.

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

Create one complete prompt per commit unit through its detail job and landing script. The landing script owns the full compiled-prompt contract; the coordinator must not read or reproduce that contract during routing. In `lean`, keep the task file focused on the compiled prompt instead of duplicating its sections around it.

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
