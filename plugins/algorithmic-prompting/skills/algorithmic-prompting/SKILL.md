---
name: algorithmic-prompting
description: Turn a software goal into a dependency-aware plan with parallel work lanes, atomic commit units, a clickable task index, coding-agent prompts, and human-approved integration guidance. Use for implementation planning, specs, ADRs, issue breakdowns, parallel agent work, worktree coordination, or merge sequencing.
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

1. Inspect the request, repository guidance, relevant design documents, and affected code.
2. Choose the fewest broad lanes that expose safe parallel work. Give each lane a clear input, ownership boundary, validation profile, and mergeable output.
3. Split each lane into the fewest atomic commit units that make the history understandable and revertible, usually one to three.
4. Give every unit a stable `<LANE>-<NN>` coordination ID and a human-readable commit intent.
5. Add a hard edge only when the successor cannot pass its completion gate without the predecessor.
6. Record likely file overlap as a collision, not automatically as a dependency.
7. Reject cycles. If a collapsed lane graph cycles, merge coupled lanes or isolate a small shared prerequisite.

Keep implementation and focused tests in the same commit unit. Do not create separate nodes for routine steps, individual files, formatting, or generated output unless they are independently valuable.

Use [references/plan-schema.md](references/plan-schema.md) for the persisted plan. Run `scripts/graph_ready.py <plan.json>` to validate it and calculate ready lanes and tasks.

## Create the task artifacts

Always persist the plan in a temporary directory outside the repository unless the human requests a durable location. Then run:

```text
scripts/render_task_files.py <plan.json> [--output-dir <existing-directory>]
```

Every plan, including a one-task plan, must produce:

- `00-task-index.md`
- One kebab-case Markdown file per task
- `.task-files.json`
- A conversation summary with task links and Mermaid topology

Paste the conversation summary into chat and include the index link. Reuse the same output directory when the plan changes so stable task links remain stable.

## Advance work with human approval

Use incomplete hard prerequisites to calculate the ready queue.

1. Show ready lanes and ready commit units.
2. Show material collisions and propose the widest safe parallel batch.
3. Ask the human to approve the batch in natural language.
4. After approval, finalize the selected prompts and branch assignments.
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

Create one prompt per commit unit. Follow [references/coding-agent-prompt.md](references/coding-agent-prompt.md).

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
