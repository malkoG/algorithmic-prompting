# Contributing

Squire is a Claude Code / Codex plugin marketplace: a `.claude-plugin/marketplace.json` and
`.agents/plugins/marketplace.json` pair listing plugins under `plugins/`, each shipping one or more
`SKILL.md`-driven skills. This document records the patterns already used by
`plugins/algorithmic-prompting` and `plugins/wireframe-picker`, and the baseline engineering
principles that apply regardless of what a given change touches. Follow them when adding or editing
a skill, script, or manifest, so new work stays consistent with what's already here.

## Contents

- [§0 Guiding principles](#p0)
- [§1 Repository structure](#p1)
- [§2 Skill conventions](#p2)
- [§3 Versioning](#p3)

<a id="p0"></a>

## §0 Guiding principles

**Human-controlled, not autonomous.** Squire's own README states its purpose: agent plugins that
"prepare the field, coordinate specialized agents, and surface decisions while the human remains in
control." Both existing skills enforce this directly rather than treating it as a slogan —
`algorithmic-prompting` never authorizes a merge, push, or repository mutation without an explicit
human approval step, and `wireframe-picker` never merges or deletes a worktree without one either.
A new skill that lets an agent finalize an irreversible action on its own defeats the point of this
marketplace, regardless of how much friction that removes.

**Validate at boundaries, preserve error context.** Every Python script's entry points validate
their input immediately (`graph_ready.py`'s `load_plan`, `land_task_detail.py`'s `string_list`) and
raise with the original failure folded into the message — `fail(f"cannot read plan: {exc}")` — never
a bare re-raise or a swallowed exception. Internal call graphs (a landing script calling
`analyze()` on an already-validated plan) skip re-validation; only the actual entry point checks.

**Avoid premature abstraction.** Two plugins, two skills — there is no shared plugin-authoring
framework, and none should be added until a third plugin's needs actually justify one. Prefer
extending an existing skill's references/scripts over introducing a new abstraction layer for a
single use.

**Keep changes scoped and incremental.** Each landed unit of work is one focused change. Do not
fold unrelated skill edits, manifest bumps, or script refactors into the same change.

**Comment only the non-obvious why.** Existing script comments explain a constraint or a design
reason a reader wouldn't otherwise infer (`new-variant-worktree.sh`: "so parallel subagents can each
edit the same route/component without colliding"; `render_task_files.py`'s `atomic_write_text`:
"Replace a file atomically so readers never observe partial task prompts"). No comment restates what
the following line already says.

<a id="p1"></a>

## §1 Repository structure

- `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json` both list every plugin,
  once for Claude Code and once for Codex. Add a plugin to both, kept in sync.
- Each plugin directory carries its own `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`
  (the Codex manifest additionally carries `interface.*` display metadata). Both must agree on
  `name`, `version`, and `description`.
- A plugin's actual behavior lives under `skills/<skill-name>/`: `SKILL.md` (the entry point),
  `references/*.md` (detail split out of the main flow), and `scripts/*` (deterministic tooling the
  skill shells out to instead of describing in prose).

<a id="p2"></a>

## §2 Skill conventions

`SKILL.md` frontmatter is `name` + `description` only — no extra metadata. The description states
both what the skill does and when to reach for it (see either existing `SKILL.md`'s opening
frontmatter), since it's what a router uses to decide relevance.

Open with a short "Mental model" text-diagram (a `text` code block showing the shape of the
workflow as a tree) before any procedural steps — both existing skills do this immediately after
the H1.

**Fire-and-forget dispatch.** Dispatch subagents or watchers, then return control immediately
instead of blocking on a reply.

> "Dispatch attempts finish, return immediately; do not wait for messages or perform a fan-in."
> — `plugins/algorithmic-prompting/skills/algorithmic-prompting/SKILL.md`

`wireframe-picker` applies the same idea to a human reply: start a live `tail -F` watch on the
events file rather than ending the turn and waiting for the user to type something back.

**Placeholder + index + reconcile-later.** Create stable filenames and placeholders for every unit
of work up front (`00-task-index.md`, `.task-files.json`, one placeholder per task file), then only
reconcile them into a summary on a later, separate invocation — never inline with dispatch.

**Bounded writable scope, single writer per artifact.** Each dispatched worker owns exactly one
output file; anything shared (the index, the plan, another worker's file) is off limits.

> "Detail jobs must never edit `00-task-index.md`, `.task-files.json`, another task file, or the
> shared plan."
> — `plugins/algorithmic-prompting/skills/algorithmic-prompting/SKILL.md`

> "Subagents must not merge, push, or touch other variants' worktrees."
> — `plugins/wireframe-picker/skills/wireframe-picker/SKILL.md`

**Explicit negative-scope guardrails.** State exactly what a dispatched worker must not do, not
just its job — e.g. "Do not create, merge, rebase, push, or delete worktrees or branches without
matching human authorization" (`algorithmic-prompting/SKILL.md`).

**Human-gated approval before an irreversible action.** Branch creation, merges, and deletes all
wait for an explicit human confirmation step before executing, never inferred from an unrelated
reply.

> "Do this only after explicit human confirmation of the choice."
> — `plugins/wireframe-picker/skills/wireframe-picker/SKILL.md` (on `resolve-variant.sh`)

**One flag controls output detail, never scope.** `algorithmic-prompting`'s `lean`/`balanced`/
`thorough` prompt profile changes how much detail a landed prompt carries; it never skips a step or
changes which files get written.

<a id="p3"></a>

## §3 Versioning

As of `0.9.0`, every plugin in this repository shares one `X.Y.Z` string, set identically across
`plugins/<name>/.claude-plugin/plugin.json`, `plugins/<name>/.codex-plugin/plugin.json`, and that
plugin's entry in both `marketplace.json` files — six locations in total for the current two
plugins. A change to any one plugin bumps the version everywhere, even for a plugin whose own code
didn't change this release, so the string never drifts out of sync across files or plugins.

Historical tags (`v0.5.0`–`v0.8.0`) predate this convention and the current multi-plugin marketplace
layout, tagging the repository as a whole before `plugins/` existed. No repo-wide tag has been cut
since; cut one (`vX.Y.Z`) on the release commit that unifies the version bump, rather than tagging
per plugin.
