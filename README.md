# Algorithmic Prompting

Turn a software goal into parallel, commit-ready work that coding agents can execute and a human can control.

## Mental model

```text
Goal
└── Lanes — work that can proceed independently
    └── Commit units — one task, one prompt, one commit

Dependencies determine what is ready next.
```

Lane names come from the project rather than a fixed technology or product taxonomy.

## What you get

- A clickable task index for every plan
- A dependency graph showing parallel and waiting work
- One bounded coding-agent prompt per commit unit
- Clear start, commit, and integration handoffs

## Workflow

1. Describe the goal or provide a spec.
2. Review the proposed lanes, commit units, and dependencies.
3. Approve the next ready batch.
4. Integrate completed commits and continue with newly ready work.

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
