#!/usr/bin/env python3
"""Render a lane-aware plan as compact clickable Markdown task files."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from graph_ready import DONE, analyze, load_plan


INDEX_NAME = "00-task-index.md"
MANIFEST_NAME = ".task-files.json"
PLACEHOLDER_MARKER = "<!-- algorithmic-prompting:placeholder -->"


def one_line(value: object, fallback: str = "Not specified") -> str:
    text = " ".join(str(value or "").split())
    return text or fallback


def slugify(value: object, limit: int | None = None) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if limit is not None:
        text = text[:limit].rstrip("-")
    return text or "task"


def bullet_list(values: object) -> str:
    if not isinstance(values, list) or not values:
        return "- None"
    return "\n".join(f"- {one_line(value)}" for value in values)


def atomic_write_text(path: Path, content: str) -> None:
    """Replace a file atomically so readers never observe partial task prompts."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def task_prompt_seed(task: dict) -> str:
    """Return only the task-specific reasoning seed; the renderer supplies the contract."""
    return str(task.get("prompt_seed", task.get("draft_prompt", ""))).strip()


def task_prompt_profile(plan: dict, task: dict) -> str:
    return str(task.get("prompt_profile", plan.get("prompt_profile", "lean")))


def render_agent_prompt(
    plan: dict,
    task: dict,
    lane: dict,
    dependencies: list[dict],
    collisions: list[dict],
    ready: set[str],
) -> str:
    """Compile a complete, self-contained worker prompt from one shared plan."""
    task_id = task["id"]
    by_id = {item["id"]: item for item in plan["tasks"]}
    prerequisite_edges = [edge for edge in dependencies if edge.get("to") == task_id]
    predecessors = [edge["from"] for edge in prerequisite_edges]
    waiting_for = [
        predecessor
        for predecessor in predecessors
        if by_id[predecessor].get("status", "planned") not in DONE
    ]

    dependency_lines = [
        f"{edge['from']} — {one_line(edge.get('reason'), 'required predecessor')}"
        for edge in prerequisite_edges
    ]
    risk_lines = []
    for collision in collisions:
        if task_id not in collision.get("tasks", []):
            continue
        peers = [peer for peer in collision["tasks"] if peer != task_id]
        risk_lines.append(
            f"{', '.join(peers)} — {one_line(collision.get('surface'))} "
            f"({one_line(collision.get('risk'), 'unspecified risk')})"
        )
    risk_lines.extend(task.get("detail_risks", []))

    base_branch = one_line(task.get("base_branch", lane.get("base_branch")), "Coordinator will assign")
    base_sha = one_line(task.get("base_sha", lane.get("base_sha")), "Coordinator will provide")
    child_branch = one_line(
        task.get("assigned_branch", lane.get("assigned_branch")),
        "Coordinator will assign",
    )
    worktree = one_line(task.get("worktree", lane.get("worktree")), "Coordinator will assign")
    integration_target = one_line(
        task.get("integration_target", lane.get("integration_target", lane.get("base_branch"))),
        "Coordinator will assign",
    )
    readiness = (
        "Ready: no incomplete hard prerequisites."
        if task_id in ready
        else f"Wait for: {', '.join(waiting_for)}."
        if waiting_for
        else f"Current status: {one_line(task.get('status'), 'planned')}."
    )

    context_values = task.get("context", plan.get("context"))
    if isinstance(context_values, list):
        context = bullet_list(context_values)
    elif context_values:
        context = one_line(context_values)
    else:
        context = f"Goal: {one_line(plan.get('goal'), 'Complete the requested change.')}"

    scope_values = task.get("scope")
    if not isinstance(scope_values, list) or not scope_values:
        scope_values = [one_line(task.get("outcome"), task.get("title", "Task outcome"))]
    out_of_scope = task.get("out_of_scope")
    if not isinstance(out_of_scope, list) or not out_of_scope:
        out_of_scope = ["Sibling task work", "Unrelated refactors or cleanup"]
    acceptance = task.get("acceptance_criteria")
    if not isinstance(acceptance, list) or not acceptance:
        acceptance = [one_line(task.get("completion_gate"))]

    if task_prompt_profile(plan, task) == "lean":
        risk_section = f"\nRisks\n{bullet_list(risk_lines)}\n" if risk_lines else ""
        return f"""Implement {task_id}: {one_line(task.get('outcome'), task.get('title', 'Task outcome'))}

Lane: {task['lane']} — {one_line(lane.get('input'), 'accepted prerequisites')} → {one_line(lane.get('output'), lane.get('scope'))}
Prerequisites: {', '.join(dependency_lines) if dependency_lines else 'None'}. {readiness}

Guidance
{one_line(task_prompt_seed(task), 'Implement the stated outcome within the declared scope.')}

Scope
{bullet_list(scope_values)}
- Likely files: {', '.join(task.get('files', [])) or 'Inspect the declared lane ownership.'}

Avoid
{bullet_list(out_of_scope)}
{risk_section}
Done
{bullet_list(acceptance)}

Checks
{bullet_list(task.get('validation'))}

Execution
- Use {child_branch} from {base_branch} at {base_sha}; worktree: {worktree}; integration target: {integration_target}.
- This draft does not authorize repository mutations. Before editing, verify branch and HEAD. Create only the assigned branch after authorization at the exact base SHA; otherwise stop.
- After checks pass, create exactly one focused commit. Use an outcome-based subject plus two to four bullet lines; omit task IDs, branch names, and worktree names.
- Return branch, full commit SHA, changed files, checks, assumptions, and risks. Do not merge, rebase, push, or delete the branch or worktree.
"""

    module_line = f"- Module: {task['module']}\n" if task.get("module") else ""
    return f"""Implement {task_id}: {one_line(task.get('outcome'), task.get('title', 'Task outcome'))}

Lane
- Name: {task['lane']}
{module_line}- Contract: {one_line(lane.get('input'), 'accepted prerequisites')} → {one_line(lane.get('output'), lane.get('scope'))}
- Ownership: {', '.join(lane.get('paths', []))}
- Validation profile: {', '.join(lane.get('validation', []))}

Commit unit
- Coordination ID: {task_id}
- Commit intent: {one_line(task.get('commit_intent'), task.get('title', 'Task outcome'))}
- Prerequisites: {', '.join(predecessors) if predecessors else 'None'}
- Readiness: {readiness}

Context
{context}

Task-specific guidance
{one_line(task_prompt_seed(task), 'Implement the stated outcome within the declared scope.')}

Execution
- Base branch: {base_branch}
- Exact base SHA: {base_sha}
- Child branch: {child_branch}
- Worktree: {worktree}
- Integration target: {integration_target}
- This plan does not authorize branch creation or repository mutations until the coordinator approves this task.

Scope
{bullet_list(scope_values)}
- Likely files: {', '.join(task.get('files', [])) or 'Inspect the declared lane ownership.'}

Out of scope
{bullet_list(out_of_scope)}

Hard dependencies
{bullet_list(dependency_lines)}

Coordination risks
{bullet_list(risk_lines)}

Acceptance criteria
{bullet_list(acceptance)}

Validation
Lane checks:
{bullet_list(lane.get('validation'))}

Task checks:
{bullet_list(task.get('validation'))}

Completion gate
{one_line(task.get('completion_gate'))}

Branch safety
- Inspect the current branch and HEAD before editing.
- Continue when already on the assigned child branch.
- Create only the assigned child branch when authorized and detached at the exact base SHA.
- Otherwise stop and report the mismatch.
- Do not advance the parent branch.

Commit and handoff
After successful validation, create exactly one focused commit for this unit. Do not combine it with another task or split it across commits.

Use an outcome-based imperative subject, a blank line, and two to four bullet lines describing meaningful changes and validation. Do not include coordination IDs, branch names, or worktree names.

Return the child branch, full commit SHA, changed files, validation results, assumptions, and remaining risks. Do not merge, rebase, push, or delete the branch or worktree. If a prerequisite is missing, validation fails, scope expands materially, or a collision makes the work unsafe, stop without creating a success commit.
"""


def load_manifest(output_dir: Path) -> dict[str, str]:
    path = output_dir / MANIFEST_NAME
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(value, dict):
        return {}
    return {
        str(task_id): filename
        for task_id, filename in value.items()
        if isinstance(filename, str)
        and Path(filename).name == filename
        and filename.endswith(".md")
        and filename != INDEX_NAME
    }


def task_filename(task: dict, manifest: dict[str, str]) -> str:
    task_id = task["id"]
    if task_id in manifest:
        return manifest[task_id]
    return f"{slugify(task_id)}-{slugify(task.get('title', 'task'), 60)}.md"


def render_placeholder(plan: dict, task: dict, lane: dict, ready: set[str]) -> str:
    status = "ready" if task["id"] in ready else task.get("status", "planned")
    return f"""# {task['id']} — {one_line(task.get('title'), 'Task')}

{PLACEHOLDER_MARKER}

- Lane: {task['lane']}
- Lane scope: {one_line(lane.get('scope'))}
- Execution status: {status}
- Prompt status: detailing
- Prompt profile: {task_prompt_profile(plan, task)}
- Commit intent: {one_line(task.get('commit_intent'), task.get('title', 'Task outcome'))}

The complete coding-agent prompt is being prepared. This file will be replaced atomically when its independent detail job finishes.
"""


def render_detail_review(task: dict) -> str:
    dependencies = [
        f"{item.get('from')} → {item.get('to')} — {one_line(item.get('reason'))}"
        for item in task.get("detail_proposed_dependencies", [])
        if isinstance(item, dict)
    ]
    collisions = [
        f"{', '.join(item.get('tasks', []))} — {one_line(item.get('surface'))} "
        f"({one_line(item.get('risk'), 'unspecified risk')})"
        for item in task.get("detail_proposed_collisions", [])
        if isinstance(item, dict) and isinstance(item.get("tasks"), list)
    ]
    uncertainties = task.get("detail_uncertainties", [])
    if not dependencies and not collisions and not uncertainties:
        return ""
    return f"""
## Detail review

### Proposed dependencies

{bullet_list(dependencies)}

### Proposed collisions

{bullet_list(collisions)}

### Uncertainties

{bullet_list(uncertainties)}
"""


def render_task(
    plan: dict,
    task: dict,
    lane: dict,
    dependencies: list[dict],
    collisions: list[dict],
    ready: set[str],
) -> str:
    task_id = task["id"]
    predecessors = [edge["from"] for edge in dependencies if edge.get("to") == task_id]
    waiting_for = [
        predecessor
        for predecessor in predecessors
        if next(item for item in plan["tasks"] if item["id"] == predecessor).get("status", "planned") not in DONE
    ]
    risks = []
    for collision in collisions:
        if task_id in collision.get("tasks", []):
            peers = [peer for peer in collision["tasks"] if peer != task_id]
            risks.append(
                f"{', '.join(peers)} — {one_line(collision.get('surface'))} ({one_line(collision.get('risk'), 'unspecified risk')})"
            )
    status = "ready" if task_id in ready else task.get("status", "planned")
    prompt = render_agent_prompt(plan, task, lane, dependencies, collisions, ready)
    detail_review = render_detail_review(task)
    profile = task_prompt_profile(plan, task)
    if profile == "lean":
        return f"""# {task_id} — {one_line(task.get('title'), 'Task')}

- Lane: {task['lane']}
- Status: {status}
- Prompt status: ready
- Prompt profile: lean

## Coding-agent prompt

```text
{prompt}
```
{detail_review}

## Handoff

- Branch and full commit SHA:
- Checks and risks:
"""

    module_line = f"- Module: {task['module']}\n" if task.get("module") else ""
    return f"""# {task_id} — {one_line(task.get('title'), 'Task')}

- Lane: {task['lane']}
{module_line}- Lane scope: {one_line(lane.get('scope'))}
- Status: {status}
- Prompt status: ready
- Prompt profile: {profile}
- Dependencies: {', '.join(predecessors) if predecessors else 'None'}
- Waiting for: {', '.join(waiting_for) if waiting_for else 'None'}
- Assigned branch: {one_line(task.get('assigned_branch', lane.get('assigned_branch')), 'Coordinator will assign')}
- Commit intent: {one_line(task.get('commit_intent'), task.get('title', 'Task outcome'))}

## Outcome

{one_line(task.get('outcome'), task.get('title', 'Task outcome'))}

## Likely files

{bullet_list(task.get('files'))}

## Collision risks

{bullet_list(risks)}

## Validation

### Lane profile

{bullet_list(lane.get('validation'))}

### Task checks

{bullet_list(task.get('validation'))}

## Completion gate

{one_line(task.get('completion_gate'))}

## Commit contract

- End this successfully validated task with exactly one focused commit.
- Keep this task node and its resulting commit one-to-one; do not combine or split it.
- Do not mention internal task or graph identifiers in the commit message.
- Use an outcome-based subject, a blank line, and two to four bullet lines.

## Coding-agent prompt

```text
{prompt}
```
{detail_review}

## Handoff

- Child branch:
- Commit SHA:
- Commit subject:
- Commit body bullets:
- Files changed:
- Validation results:
- Assumptions and risks:
"""


def category(task: dict, ready: set[str]) -> str:
    if task["id"] in ready:
        return "Ready"
    status = task.get("status", "planned")
    if status in DONE:
        return "Completed"
    if status == "active":
        return "Active"
    if status == "blocked":
        return "Blocked"
    return "Waiting"


def render_index(
    plan: dict,
    filenames: dict[str, str],
    ready: set[str],
    placeholders: bool = False,
) -> str:
    grouped: dict[str, dict[str, dict[str, list[dict]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    for task in plan["tasks"]:
        grouped[category(task, ready)][task["lane"]][task.get("module", "Tasks")].append(task)
    lines = [f"# {one_line(plan.get('goal'), 'Task plan')}", ""]
    for heading in ("Ready", "Active", "Waiting", "Blocked", "Completed"):
        if heading not in grouped:
            continue
        lines.extend([f"## {heading}", ""])
        for lane_id in sorted(grouped[heading]):
            lines.extend([f"### {lane_id}", ""])
            for module_id in sorted(grouped[heading][lane_id]):
                if module_id != "Tasks":
                    lines.extend([f"#### {module_id}", ""])
                for task in sorted(grouped[heading][lane_id][module_id], key=lambda item: item["id"]):
                    label = f"{task['id']} — {one_line(task.get('title'), 'Task')}"
                    lines.append(f"- [{label}]({filenames[task['id']]})")
                lines.append("")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def task_link(task: dict, filenames: dict[str, str], output_dir: Path) -> str:
    label = f"{task['id']} — {one_line(task.get('title'), 'Task')}"
    path = output_dir / filenames[task["id"]]
    return f"[{label}](<{path}>)"


def mermaid_token(prefix: str, value: object) -> str:
    token = re.sub(r"[^A-Za-z0-9_]", "_", str(value))
    return f"{prefix}_{token}"


def mermaid_label(value: object) -> str:
    return (
        one_line(value)
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_task_mermaid(plan: dict) -> str:
    """Render the full hard-dependency topology with lane partitions."""
    tasks = sorted(plan["tasks"], key=lambda item: item["id"])
    task_ids = {task["id"] for task in tasks}
    compact_labels = len(tasks) > 12
    grouped: dict[str, list[dict]] = defaultdict(list)
    for task in tasks:
        grouped[task["lane"]].append(task)

    lines = ["```mermaid", "flowchart LR"]
    for lane_id in sorted(grouped):
        lane_token = mermaid_token("lane", lane_id)
        lines.append(f'  subgraph {lane_token}["{mermaid_label(lane_id)}"]')
        for task in grouped[lane_id]:
            node = mermaid_token("task", task["id"])
            if compact_labels:
                label = mermaid_label(task["id"])
            else:
                label = f"{mermaid_label(task['id'])}<br/>{mermaid_label(task.get('title', 'Task'))}"
            lines.append(f'    {node}["{label}"]')
        lines.append("  end")

    for edge in plan.get("dependencies", []):
        predecessor = edge.get("from")
        successor = edge.get("to")
        if predecessor in task_ids and successor in task_ids:
            lines.append(
                f"  {mermaid_token('task', predecessor)} --> {mermaid_token('task', successor)}"
            )

    collision_pairs: set[tuple[str, str]] = set()
    for collision in plan.get("collisions", []):
        peers = sorted(task_id for task_id in collision.get("tasks", []) if task_id in task_ids)
        for index, left in enumerate(peers):
            for right in peers[index + 1 :]:
                pair = (left, right)
                if pair in collision_pairs:
                    continue
                collision_pairs.add(pair)
                lines.append(
                    f"  {mermaid_token('task', left)} -. collision .-> {mermaid_token('task', right)}"
                )

    lines.append("```")
    return "\n".join(lines)


def render_module_mermaid(plan: dict, state: dict) -> str:
    """Render the quotient DAG: modules are nodes, cross-module task edges are collapsed."""
    modules = sorted(plan.get("modules", []), key=lambda item: item["id"])
    grouped: dict[str, list[dict]] = defaultdict(list)
    for module in modules:
        grouped[module["lane"]].append(module)

    lines = ["```mermaid", "flowchart LR"]
    for lane_id in sorted(grouped):
        lines.append(f'  subgraph {mermaid_token("lane", lane_id)}["{mermaid_label(lane_id)}"]')
        for module in grouped[lane_id]:
            label = f"{mermaid_label(module['id'])}<br/>{mermaid_label(module.get('output', 'Module output'))}"
            lines.append(f'    {mermaid_token("module", module["id"])}["{label}"]')
        lines.append("  end")
    for edge in state.get("module_dependencies", []):
        lines.append(
            f"  {mermaid_token('module', edge['from'])} --> {mermaid_token('module', edge['to'])}"
        )
    lines.append("```")
    return "\n".join(lines)


def render_lane_mermaid(plan: dict, state: dict) -> str:
    """Render broad execution lanes and their collapsed cross-lane dependencies."""
    lines = ["```mermaid", "flowchart LR"]
    for lane in sorted(plan["lanes"], key=lambda item: item["id"]):
        label = f"{mermaid_label(lane['id'])}<br/>{mermaid_label(lane.get('output', lane.get('scope', 'Lane output')))}"
        lines.append(f'  {mermaid_token("lane", lane["id"])}["{label}"]')
    for edge in state.get("lane_dependencies", []):
        lines.append(f"  {mermaid_token('lane', edge['from'])} --> {mermaid_token('lane', edge['to'])}")
    lines.append("```")
    return "\n".join(lines)


def module_task_notation(module_id: str, plan: dict) -> str:
    task_ids = sorted(task["id"] for task in plan["tasks"] if task.get("module") == module_id)
    if not task_ids:
        return "None"
    internal_edges = [
        (edge.get("from"), edge.get("to"))
        for edge in plan.get("dependencies", [])
        if edge.get("from") in task_ids and edge.get("to") in task_ids
    ]
    if len(task_ids) > 1 and len(internal_edges) == len(task_ids) - 1:
        successors = {source: target for source, target in internal_edges}
        targets = {target for _, target in internal_edges}
        starts = [task_id for task_id in task_ids if task_id not in targets]
        if len(starts) == 1 and len(successors) == len(internal_edges):
            ordered = [starts[0]]
            while ordered[-1] in successors:
                ordered.append(successors[ordered[-1]])
            if len(ordered) == len(task_ids):
                return " → ".join(ordered)
    return ", ".join(task_ids)


def lane_task_notation(lane_id: str, plan: dict) -> str:
    task_ids = sorted(task["id"] for task in plan["tasks"] if task["lane"] == lane_id)
    if not task_ids:
        return "None"
    internal_edges = [
        (edge.get("from"), edge.get("to"))
        for edge in plan.get("dependencies", [])
        if edge.get("from") in task_ids and edge.get("to") in task_ids
    ]
    if len(task_ids) > 1 and len(internal_edges) == len(task_ids) - 1:
        successors = {source: target for source, target in internal_edges}
        targets = {target for _, target in internal_edges}
        starts = [task_id for task_id in task_ids if task_id not in targets]
        if len(starts) == 1 and len(successors) == len(internal_edges):
            ordered = [starts[0]]
            while ordered[-1] in successors:
                ordered.append(successors[ordered[-1]])
            if len(ordered) == len(task_ids):
                return " → ".join(ordered)
    return ", ".join(task_ids)


def render_lane_cards(plan: dict, state: dict) -> str:
    ready = set(state.get("lane_ready", []))
    completed = set(state.get("lane_completed", []))
    outgoing: dict[str, list[str]] = defaultdict(list)
    for edge in state.get("lane_dependencies", []):
        outgoing[edge["from"]].append(edge["to"])
    blocks: list[str] = []
    for lane in sorted(plan["lanes"], key=lambda item: item["id"]):
        status = "ready" if lane["id"] in ready else "completed" if lane["id"] in completed else "waiting"
        lane_task_count = sum(task["lane"] == lane["id"] for task in plan["tasks"])
        task_label = "Task" if lane_task_count == 1 else "Tasks"
        lines = [
            f"Lane: {lane['id']} — {status}",
            f"Input: {one_line(lane.get('input'), 'goal and accepted prerequisites')}",
            f"Owns: {', '.join(lane.get('paths', []))}",
            f"{task_label}: {lane_task_notation(lane['id'], plan)}",
            f"Output: {one_line(lane.get('output'), lane.get('scope'))}",
        ]
        branch = lane.get("assigned_branch")
        commit_sha = lane.get("commit_sha")
        target = lane.get("base_branch")
        if lane["id"] in ready and target:
            lines.append(f"Start: {lane['id']} from {target}")
        if branch and commit_sha and target:
            lines.append(f"Merge: {branch} @ {commit_sha} → {target}")
        if outgoing[lane["id"]]:
            lines.append(f"Next: {', '.join(sorted(outgoing[lane['id']]))}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def render_module_cards(plan: dict, state: dict) -> str:
    ready = set(state.get("module_ready", []))
    completed = set(state.get("module_completed", []))
    outgoing: dict[str, list[str]] = defaultdict(list)
    for edge in state.get("module_dependencies", []):
        outgoing[edge["from"]].append(edge["to"])
    modules = sorted(plan.get("modules", []), key=lambda item: item["id"])
    if len(modules) > 8:
        visible = [
            module
            for module in modules
            if module["id"] in ready or module.get("status") in {"active", "blocked"}
        ]
    else:
        visible = modules
    blocks: list[str] = []
    for module in visible:
        status = "ready" if module["id"] in ready else "completed" if module["id"] in completed else module.get("status", "waiting")
        lines = [
            f"Module: {module['id']} — {status}",
            f"Input: {one_line(module.get('input'))}",
            f"Owns: {', '.join(module.get('owns', []))}",
            f"Tasks: {module_task_notation(module['id'], plan)}",
            f"Output: {one_line(module.get('output'))}",
        ]
        branch = module.get("assigned_branch")
        commit_sha = module.get("commit_sha")
        target = module.get("base_branch")
        if module["id"] in ready and target:
            lines.append(f"Start: {module['id']} from {target}")
        if branch and commit_sha and target:
            lines.append(f"Merge: {branch} @ {commit_sha} → {target}")
        if outgoing[module["id"]]:
            lines.append(f"Next: {', '.join(sorted(outgoing[module['id']]))}")
        blocks.append("\n".join(lines))
    if len(modules) > 8:
        waiting_count = sum(
            module["id"] not in ready
            and module["id"] not in completed
            and module.get("status", "planned") not in {"active", "blocked"}
            for module in modules
        )
        blocks.append(f"Waiting modules: {waiting_count} · Completed modules: {len(completed)}")
    return "\n\n".join(blocks)


def render_conversation_summary(
    plan: dict,
    filenames: dict[str, str],
    ready: set[str],
    output_dir: Path,
    state: dict,
    placeholders: bool = False,
) -> str:
    """Render a paste-ready overview so the index is an optional deep dive."""
    tasks = sorted(plan["tasks"], key=lambda item: item["id"])
    categories = {task["id"]: category(task, ready) for task in tasks}
    counts = Counter(categories.values())
    ordered_statuses = ("Ready", "Active", "Waiting", "Blocked", "Completed")
    status_line = " · ".join(
        f"{counts[status]} {status.lower()}" for status in ordered_statuses if counts[status]
    )

    lane_totals = Counter(task["lane"] for task in tasks)
    lane_ready = Counter(task["lane"] for task in tasks if categories[task["id"]] == "Ready")
    lane_line = " · ".join(
        f"{lane} {lane_ready[lane]} ready/{lane_totals[lane]} total" for lane in sorted(lane_totals)
    )
    plan_profile = task_prompt_profile(plan, {})
    profile_overrides = [
        f"{task['id']}={task['prompt_profile']}"
        for task in tasks
        if task.get("prompt_profile") and task["prompt_profile"] != plan_profile
    ]
    profile_line = (
        f"{plan_profile}; overrides: {', '.join(profile_overrides)}"
        if profile_overrides
        else plan_profile
    )

    lines = [
        f"**Plan:** {one_line(plan.get('goal'), 'Task plan')}",
        f"**Status:** {status_line or 'No tasks'}",
        f"**Lanes:** {lane_line or 'None'}",
        f"**Prompt profile:** {profile_line}",
        "",
    ]
    if placeholders:
        lines.extend(["**Prompt details:** queued; task files land independently", ""])
    if plan.get("modules"):
        lines.extend(["**Modules**", "", render_module_cards(plan, state), ""])
    else:
        lines.extend(["**Execution lanes**", "", render_lane_cards(plan, state), ""])
    if len(tasks) <= 12:
        lines.append("**Tasks**")
        lines.append("")
        for task in tasks:
            lines.append(f"- {task_link(task, filenames, output_dir)} — {categories[task['id']].lower()}")
    else:
        for status in ("Ready", "Active", "Blocked"):
            selected = [task for task in tasks if categories[task["id"]] == status]
            if not selected:
                continue
            lines.extend([f"**{status}**", ""])
            for task in selected:
                lines.append(f"- {task_link(task, filenames, output_dir)}")
            lines.append("")
        lines.append(f"Waiting: {counts['Waiting']} · Completed: {counts['Completed']}")

    lines.extend(
        [
            "",
            "**Topology**",
            "",
            render_module_mermaid(plan, state)
            if plan.get("modules")
            else render_lane_mermaid(plan, state)
            if len(plan["lanes"]) > 1
            else render_task_mermaid(plan),
            "",
            f"[Open full task index](<{output_dir / INDEX_NAME}>)",
        ]
    )
    return "\n".join(lines).rstrip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path, help="path to plan JSON")
    parser.add_argument("--output-dir", type=Path, help="reuse an existing task-file directory")
    parser.add_argument(
        "--placeholders",
        action="store_true",
        help="create the index and stable placeholder task files without rendering full prompts",
    )
    args = parser.parse_args()

    plan = load_plan(args.plan)
    state = analyze(plan)
    if not state["valid_dag"]:
        cycles = state["cyclic_tasks"] + state.get("cyclic_lanes", []) + state.get("cyclic_modules", [])
        raise SystemExit(f"cannot render cyclic plan: {', '.join(cycles)}")

    if args.output_dir:
        output_dir = args.output_dir.expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        prefix = f"algorithmic-prompting-{slugify(plan.get('goal_slug', plan.get('goal', 'plan')), 32)}-"
        output_dir = Path(tempfile.mkdtemp(prefix=prefix)).resolve()

    manifest = load_manifest(output_dir)
    filenames = {task["id"]: task_filename(task, manifest) for task in plan["tasks"]}
    if len(set(filenames.values())) != len(filenames):
        raise SystemExit("task filenames are not unique")

    lanes = {lane["id"]: lane for lane in plan["lanes"]}
    ready = set(state["ready"])
    for task in plan["tasks"]:
        path = output_dir / filenames[task["id"]]
        if args.placeholders:
            if path.exists() and PLACEHOLDER_MARKER not in path.read_text(encoding="utf-8"):
                continue
            content = render_placeholder(plan, task, lanes[task["lane"]], ready)
        else:
            content = render_task(
                plan,
                task,
                lanes[task["lane"]],
                plan.get("dependencies", []),
                plan.get("collisions", []),
                ready,
            )
        atomic_write_text(path, content)

    atomic_write_text(
        output_dir / INDEX_NAME,
        render_index(plan, filenames, ready, placeholders=args.placeholders),
    )
    atomic_write_text(output_dir / MANIFEST_NAME, json.dumps(filenames, indent=2, sort_keys=True) + "\n")
    summary = render_conversation_summary(
        plan,
        filenames,
        ready,
        output_dir,
        state,
        placeholders=args.placeholders,
    )
    print(
        json.dumps(
            {
                "directory": str(output_dir),
                "index": str(output_dir / INDEX_NAME),
                "tasks": filenames,
                "mode": "placeholders" if args.placeholders else "complete",
                "conversation_summary": summary,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
