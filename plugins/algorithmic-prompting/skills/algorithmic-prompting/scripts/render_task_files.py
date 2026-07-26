#!/usr/bin/env python3
"""Render a lane-aware plan as compact clickable Markdown task files."""

from __future__ import annotations

import argparse
import json
import re
import tempfile
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from graph_ready import DONE, analyze, load_plan


INDEX_NAME = "00-task-index.md"
MANIFEST_NAME = ".task-files.json"


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
    prompt = str(task.get("draft_prompt", "")).strip()
    return f"""# {task_id} — {one_line(task.get('title'), 'Task')}

- Lane: {task['lane']}
- Lane scope: {one_line(lane.get('scope'))}
- Status: {status}
- Dependencies: {', '.join(predecessors) if predecessors else 'None'}
- Waiting for: {', '.join(waiting_for) if waiting_for else 'None'}
- Assigned branch: {one_line(task.get('assigned_branch'), 'Coordinator will assign')}

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

## Coding-agent prompt

```text
{prompt}
```

## Handoff

- Child branch:
- Commit SHA:
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


def render_index(plan: dict, filenames: dict[str, str], ready: set[str]) -> str:
    grouped: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for task in plan["tasks"]:
        grouped[category(task, ready)][task["lane"]].append(task)
    lines = [f"# {one_line(plan.get('goal'), 'Task plan')}", ""]
    for heading in ("Ready", "Active", "Waiting", "Blocked", "Completed"):
        if heading not in grouped:
            continue
        lines.extend([f"## {heading}", ""])
        for lane_id in sorted(grouped[heading]):
            lines.extend([f"### {lane_id}", ""])
            for task in sorted(grouped[heading][lane_id], key=lambda item: item["id"]):
                label = f"{task['id']} — {one_line(task.get('title'), 'Task')}"
                lines.append(f"- [{label}]({filenames[task['id']]})")
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


def render_mermaid(plan: dict) -> str:
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


def render_conversation_summary(
    plan: dict,
    filenames: dict[str, str],
    ready: set[str],
    output_dir: Path,
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

    lines = [
        f"**Plan:** {one_line(plan.get('goal'), 'Task plan')}",
        f"**Status:** {status_line or 'No tasks'}",
        f"**Lanes:** {lane_line or 'None'}",
        "",
    ]
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
            render_mermaid(plan),
            "",
            f"[Open full task index](<{output_dir / INDEX_NAME}>)",
        ]
    )
    return "\n".join(lines).rstrip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path, help="path to plan JSON")
    parser.add_argument("--output-dir", type=Path, help="reuse an existing task-file directory")
    args = parser.parse_args()

    plan = load_plan(args.plan)
    state = analyze(plan)
    if not state["valid_dag"]:
        raise SystemExit(f"cannot render cyclic plan: {', '.join(state['cyclic_tasks'])}")

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
        content = render_task(
            plan,
            task,
            lanes[task["lane"]],
            plan.get("dependencies", []),
            plan.get("collisions", []),
            ready,
        )
        (output_dir / filenames[task["id"]]).write_text(content, encoding="utf-8")

    (output_dir / INDEX_NAME).write_text(render_index(plan, filenames, ready), encoding="utf-8")
    (output_dir / MANIFEST_NAME).write_text(json.dumps(filenames, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = render_conversation_summary(plan, filenames, ready, output_dir)
    print(
        json.dumps(
            {
                "directory": str(output_dir),
                "index": str(output_dir / INDEX_NAME),
                "tasks": filenames,
                "conversation_summary": summary,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
