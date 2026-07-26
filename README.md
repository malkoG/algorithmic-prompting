# Algorithmic Prompting

A ChatGPT and Codex plugin for decomposing implementation goals into lane-aware subtasks, modeling hard prerequisites and merge risks, drafting bounded coding-agent prompts, and coordinating parallel worktrees with human-in-the-loop Kahn scheduling.

## Highlights

- Architecture lanes such as `API`, `WEB`, and `SDK`
- Stable lane-aware task IDs
- Hard dependency DAGs and file-collision constraints
- Conversation-ready Mermaid topology
- Draft coding-agent prompt for every subtask
- Clickable task files for large plans
- Human-approved worktree, branch, commit, and merge coordination

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
