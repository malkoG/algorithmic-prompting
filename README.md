# Algorithmic Prompting

Turn a software goal into parallel, commit-ready work that coding agents can execute and a human can control.

## Mental model

```text
Goal
└── Map-first scan — architecture files, schemas, and file structure
    └── Provisional lanes — work that can proceed independently
        └── Commit units — one task, one prompt, one commit

Dependencies determine what is ready next.
```

Lane names come from the project rather than a fixed technology or product taxonomy.

```text
Summary and task index return first
└── Concurrent subagents verify code and land full task prompts independently
```

## What you get

- A clickable task index for every plan
- A fast provisional topology derived from high-information repository maps
- A dependency graph showing parallel and waiting work
- One bounded coding-agent prompt that lands independently per commit unit
- Concurrent prompt-detail subagents with no coordinator fan-in
- Clear start, commit, and integration handoffs

Prompt depth is selectable: `lean` (default), `balanced`, or `thorough`. The lean profile keeps each detail job and landed prompt compact; use deeper profiles only where the task benefits from more context and edge cases.

## Workflow

1. Describe the goal or provide a spec.
2. Review the provisional map-first summary, lanes, commit units, and dependencies.
3. Open stable task links as full prompts land in parallel.
4. Approve the next ready batch and integrate completed commits.

## Install

```sh
codex plugin marketplace add malkoG/algorithmic-prompting
codex plugin add algorithmic-prompting@malkog-plugins
```

Start a new ChatGPT or Codex conversation after installation.

## Update

```sh
codex plugin marketplace upgrade malkog-plugins
codex plugin add algorithmic-prompting@malkog-plugins
```
