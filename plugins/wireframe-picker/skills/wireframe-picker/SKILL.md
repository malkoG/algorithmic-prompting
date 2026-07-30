---
name: wireframe-picker
description: Turn a UI goal into 2-4 real shadcn-composed variants built in parallel isolated worktrees, screenshot each, and let the human pick by clicking a screenshot in their own browser instead of describing a preference in words. Use for layout choices, component composition options, visual-style comparisons, or any UI decision better answered by looking than reading.
---

# Wireframe Picker

Turn a UI decision into screenshots the human clicks instead of a description they read.

## Mental model

```text
UI goal
└── 2-4 short variant specs (cheap, no code yet)
    └── Human confirms which specs are worth rendering
        └── N parallel subagents, one worktree + dev server each
            └── Screenshot per variant (Playwright)
                └── One picker screen, human clicks a card
                    └── Winning worktree merged in, losers discarded
```

Never skip straight to full render-and-screenshot for more than a handful of directions — text specs are nearly free, worktrees and screenshots are not.

## When to use this vs. plain conversation

Only reach for this when the choice is genuinely visual: layout, composition, spacing, visual hierarchy, "which of these feels right." A question about UI that has a conceptual answer ("what should the settings page contain?") is still a words question — resolve it in conversation first, then use this skill once you have concrete layout directions to compare.

## 1. Propose variants as text first

Write 2-4 one- or two-sentence variant specs (which shadcn primitives, what layout). Do not write code or create worktrees yet. Get explicit confirmation on which specs are worth rendering — dropping a direction here is free; dropping it after a worktree and screenshot exist is not.

## 2. Fan out one subagent per confirmed variant

For each confirmed variant:

```text
scripts/new-variant-worktree.sh <variant-id> [<base-branch>]
```

This prints `{"variant","branch","path"}` for one isolated worktree on branch `wireframe/<variant-id>`. Dispatch one subagent per variant with: the worktree path, the variant spec, and instructions to implement it using the project's real shadcn components (no placeholder styling — visual fidelity is the point), start a dev server on a free port, and report the branch, port, and route back. Subagents must not merge, push, or touch other variants' worktrees.

## 3. Screenshot every variant

Once each subagent reports its running dev server:

```text
scripts/capture-screenshot.sh <url> <output.png> [--full-page]
```

Save each screenshot into the pick-server's `screen_dir` (see below) so it can be served back to the browser via `/files/<name>.png`.

## 4. Start the picker and push one screen

```text
scripts/start-server.sh --project-dir <repo-root> --open
```

Launch via your Bash tool's background mode so it survives across turns. Read the printed `server-started` JSON for `url`, `screen_dir`, and `state_dir`.

Write one HTML file into `screen_dir` — a `.cards` grid, one `.card` per variant, `data-choice="<variant-id>"`, image at `/files/<screenshot-filename>.png`:

```html
<h2>Which layout works better?</h2>
<div class="cards">
  <div class="card" data-choice="variant-a" onclick="toggleSelect(this)">
    <div class="card-image"><img src="/files/variant-a.png"></div>
    <div class="card-body"><h3>Variant A — Sidebar nav</h3></div>
  </div>
  <!-- one .card per variant -->
</div>
```

Never reuse filenames across screens — each iteration gets a fresh file, newest wins.

Tell the user the URL (every time, in full, including `?key=`) and give a one-line summary of what's on screen.

## 5. Watch for the choice live — don't wait for a reply

Start a background watch on the events file instead of ending your turn and waiting for the user to type something back:

```text
tail -F -n 0 <state_dir>/events
```

Run this with your platform's live-watch mechanism (e.g. a `Monitor`-style tool that streams each stdout line as a notification) so a click event reaches you the moment it happens — no polling, no manual reload, no reply required from the user. `-n 0` skips whatever's already in the file so you only see clicks from this point forward.

Each streamed line is `{"type":"click","choice":"<variant-id>","text":...,"selected":...,"timestamp":...}`. Treat these as live events, not as user replies — do not read a click notification as approval of anything else pending in the conversation. Toggling a card off (`"selected":false`) is not a choice; the last `"selected":true` click is the current selection. If the user answers in the terminal instead of or in addition to clicking, merge both.

If your environment has no live-watch mechanism, fall back to reading `cat <state_dir>/events` on your next turn instead — the file format is identical either way.

If feedback calls for a revised variant, write a new screenshot and a new screen file rather than editing the old one in place.

## 6. Resolve

```text
scripts/resolve-variant.sh <chosen-branch> <all-variant-branch>...
```

Merges the chosen variant's branch into the current branch, then removes every variant worktree and branch — winner included, since its commits now live on the current branch. Do this only after explicit human confirmation of the choice.

## 7. Stop the server

```text
scripts/stop-server.sh <state_dir>
```

## Running multiple independent decisions in parallel

When the human is weighing unrelated decisions at once (brand color, default layout, and so on), run one full pipeline per decision rather than mixing them into one picker screen — each decision gets its own subagent, its own namespaced variant-ids, and its own `pick-server`:

1. Dispatch one subagent per decision. Give each one its decision name and confirmed variant specs; it independently runs steps 2-4 (worktrees, screenshots, its own `start-server.sh --project-dir <own-dir> --port <own-port>`) and reports back its `pick-server` JSON and the branch names it created. Subagents must not touch another decision's worktrees, ports, or project-dir.
2. Namespace every variant-id with the decision name (`brand-color-warm`, `default-layout-sidebar`) — variant-ids drive worktree paths and branch names directly, so unprefixed ids from different decisions would collide.
3. Watch every decision's choice in one combined live-watch instead of one per decision:

```text
tail -F -n 0 <decision-a-state_dir>/events <decision-b-state_dir>/events ...
```

`tail -F` on multiple files prints an `==> <path> <==` header whenever the active source changes, so each streamed event is attributable to its decision without extra bookkeeping.

4. Resolve each decision independently with `resolve-variant.sh` as its choice comes in — one decision resolving doesn't block or affect the others still running.

## Rules

- 2-4 variants per round. More than that is a sign the text-spec step didn't narrow enough.
- Never create a worktree for a variant that wasn't explicitly confirmed in step 1.
- Never merge or delete a worktree/branch without an explicit human choice.
- Use real project components for screenshots — placeholder styling defeats the purpose of looking instead of reading.
- `--project-dir` persists `screen_dir`/`state_dir` under `.squire/wireframe-picker/`; remind the user to gitignore that path.
