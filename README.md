# Algorithmic Prompting

A ChatGPT and Codex plugin for decomposing implementation goals into a few broad, independently mergeable execution lanes, then coordinating parallel worktrees with human-in-the-loop Kahn scheduling.

## Highlights

- Architecture lanes such as `API`, `WEB`, and `SDK`
- Broad lanes with input, ownership, validation, and output contracts
- One worktree, branch, coarse task, and coding-agent prompt per lane by default
- A collapsed lane DAG with intentionally sparse dependencies
- Minimal task splitting: only for real prerequisite, ownership, merge, rollback, or validation boundaries
- Stable lane-aware task IDs
- Hard dependency DAGs and file-collision constraints
- Conversation-ready Mermaid topology
- Draft coding-agent prompt for every subtask
- Clickable task files for large plans
- Human-approved worktree, branch, commit, and merge coordination
- Exactly one focused commit per dispatched task, with no internal graph IDs
- Outcome-based commit subjects followed by two to four bullet lines

## Compact lane prompt

```text
Lane: API
Input: approved auth contract
Owns: api/auth/**
Task: API-01
Output: authenticated endpoint
Merge: task/authentication/api @ <full commit SHA> → feature/authentication
Next: SDK, WEB
```

Successful task commits use this shape:

```text
Add authenticated session handling

- Validate credentials and issue session tokens
- Preserve existing rejection behavior
- Cover successful and rejected sign-in flows
```

## Install from GitHub

Add this repository as a marketplace:

```sh
codex plugin marketplace add malkoG/algorithmic-prompting
```

Install the plugin:

```sh
codex plugin add algorithmic-prompting@malkog-plugins
```

Start a new ChatGPT or Codex conversation after installation so the bundled skill is loaded.

## Update

```sh
codex plugin marketplace upgrade malkog-plugins
codex plugin add algorithmic-prompting@malkog-plugins
```

## Repository layout

```text
.agents/plugins/marketplace.json
plugins/algorithmic-prompting/
├── .codex-plugin/plugin.json
└── skills/algorithmic-prompting/
```

The repository marketplace is intended for Git-based installation and team distribution. It is separate from the universal public Plugins Directory.
