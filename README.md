# Squire

Human-controlled agent workflows by Jaeyeol Lee.

## Why Squire

A squire traditionally prepared equipment, carried messages, and supported a knight throughout a campaign while the knight retained command. Squire brings that relationship to agent workflows: its plugins prepare the field, coordinate specialized agents, and surface decisions while the human remains in control.

## Algorithmic Prompting

Turn a software goal into parallel, commit-ready work that coding agents can execute and a human can control.

### Mental model

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

### What you get

- A clickable task index for every plan
- A fast provisional topology derived from intentionally structured layout
- A dependency graph showing parallel and waiting work
- One bounded coding-agent prompt that lands independently per commit unit
- One task-free whole-system overview that lands independently
- Later reconciliation of global and task-local findings
- Concurrent planning jobs with no initial coordinator fan-in
- Clear start, commit, and integration handoffs

Prompt depth is selectable: `lean` (default), `balanced`, or `thorough`. The lean profile keeps each detail job and landed prompt compact; use deeper profiles only where the task benefits from more context and edge cases.

### Workflow

1. Describe the goal or provide a spec.
2. Review the provisional routing summary, lanes, task shells, and explicit dependencies.
3. Let the system overview and full task prompts land in parallel.
4. Invoke reconciliation to review proposed graph or prompt changes.
5. Approve the next ready batch and integrate completed commits.

### Install

```sh
codex plugin marketplace add malkoG/squire
codex plugin add algorithmic-prompting@squire
```

Start a new ChatGPT or Codex conversation after installation.

### Update

```sh
codex plugin marketplace upgrade squire
codex plugin add algorithmic-prompting@squire
```

## Wireframe Picker

Turn a UI decision into real shadcn-composed variants that you choose by clicking a screenshot, not by describing a preference in words.

### Mental model

```text
UI goal
└── 2-4 short variant specs (cheap, no code yet)
    └── Human confirms which specs are worth rendering
        └── N parallel subagents, one worktree + dev server each
            └── Screenshot per variant
                └── One picker screen, human clicks a card
                    └── Winning worktree merged in, losers discarded
```

### What you get

- Cheap text variant specs before anything gets built or rendered
- Parallel, collision-free variant builds via isolated git worktrees
- Real component-composed screenshots, not placeholder mockups
- A click-to-choose picker screen served to your own browser
- The winning worktree merged in automatically; the rest discarded

### Workflow

1. Describe the UI decision you're weighing.
2. Review and confirm which of the proposed variant specs are worth rendering.
3. Let each confirmed variant build and screenshot in its own worktree.
4. Click a screenshot in your browser to choose.
5. The winning worktree is merged in; the others are cleaned up.

### Install

```sh
codex plugin marketplace add malkoG/squire
codex plugin add wireframe-picker@squire
```

Start a new ChatGPT or Codex conversation after installation.

### Update

```sh
codex plugin marketplace upgrade squire
codex plugin add wireframe-picker@squire
```
