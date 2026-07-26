# Algorithmic Prompting

Turn a software goal into parallel, commit-ready work that coding agents can execute and a human can control.

Part of **Squire** by `kodingwarrior`.

## Mental model

```text
Goal
└── Fast routing → task index and provisional DAG
    ├── N task-detail jobs → local coding prompts
    └── 1 system-overview job → global understanding
        └── Later reconciliation → reviewed graph and prompts

Dependencies determine what is ready next.
```

Lane names come from the project rather than a fixed technology or product taxonomy.

```text
Summary and task index return first
├── Task prompts land independently
└── System overview lands independently
```

## What you get

- A clickable task index for every plan
- A fast provisional topology derived from intentionally structured layout
- A dependency graph showing parallel and waiting work
- One bounded coding-agent prompt that lands independently per commit unit
- One task-free whole-system overview that lands independently
- Later reconciliation of global and task-local findings
- Concurrent planning jobs with no initial coordinator fan-in
- Clear start, commit, and integration handoffs

Prompt depth is selectable: `lean` (default), `balanced`, or `thorough`. The lean profile keeps each detail job and landed prompt compact; use deeper profiles only where the task benefits from more context and edge cases.

## Workflow

1. Describe the goal or provide a spec.
2. Review the provisional routing summary, lanes, task shells, and explicit dependencies.
3. Let the system overview and full task prompts land in parallel.
4. Invoke reconciliation to review proposed graph or prompt changes.
5. Approve the next ready batch and integrate completed commits.

## Install

```sh
codex plugin marketplace add malkoG/algorithmic-prompting
codex plugin add algorithmic-prompting@squire
```

Start a new ChatGPT or Codex conversation after installation.

## Update

```sh
codex plugin marketplace upgrade squire
codex plugin add algorithmic-prompting@squire
```
