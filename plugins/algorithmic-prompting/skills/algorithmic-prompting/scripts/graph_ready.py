#!/usr/bin/env python3
"""Validate a worktree task plan and print its Kahn ready state."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path


DONE = {"completed", "integrated"}
READY_STATUSES = {"planned", "ready"}
VALID_STATUSES = READY_STATUSES | {"active", "completed", "integrated", "blocked"}


def fail(message: str) -> None:
    raise ValueError(message)


def load_plan(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read plan: {exc}")
    if not isinstance(value, dict):
        fail("plan root must be an object")
    return value


def analyze(plan: dict) -> dict:
    lanes = plan.get("lanes")
    tasks = plan.get("tasks")
    edges = plan.get("dependencies", [])
    collisions = plan.get("collisions", [])
    if not isinstance(lanes, list) or not lanes:
        fail("lanes must be a non-empty array")
    if not isinstance(tasks, list) or not tasks:
        fail("tasks must be a non-empty array")
    if not isinstance(edges, list) or not isinstance(collisions, list):
        fail("dependencies and collisions must be arrays")

    lane_ids: set[str] = set()
    for lane in lanes:
        if not isinstance(lane, dict) or not isinstance(lane.get("id"), str):
            fail("every lane must be an object with a string id")
        lane_id = lane["id"]
        if not re.fullmatch(r"[A-Z][A-Z0-9]*", lane_id):
            fail(f"invalid lane id: {lane_id}")
        if lane_id in lane_ids:
            fail(f"duplicate lane id: {lane_id}")
        if not isinstance(lane.get("scope"), str) or not lane["scope"].strip():
            fail(f"missing non-empty scope for lane: {lane_id}")
        for field in ("paths", "validation"):
            values = lane.get(field)
            if not isinstance(values, list) or not values or any(not isinstance(value, str) or not value.strip() for value in values):
                fail(f"lane {lane_id} must have a non-empty string array for {field}")
        lane_ids.add(lane_id)

    by_id: dict[str, dict] = {}
    for task in tasks:
        if not isinstance(task, dict) or not isinstance(task.get("id"), str):
            fail("every task must be an object with a string id")
        task_id = task["id"]
        if task_id in by_id:
            fail(f"duplicate task id: {task_id}")
        lane_id = task.get("lane")
        if lane_id not in lane_ids:
            fail(f"unknown or missing lane for {task_id}: {lane_id}")
        if not re.fullmatch(rf"{re.escape(lane_id)}-\d{{2,}}", task_id):
            fail(f"task id must match its lane prefix for {task_id}: {lane_id}-<NN>")
        status = task.get("status", "planned")
        if status not in VALID_STATUSES:
            fail(f"invalid status for {task_id}: {status}")
        draft_prompt = task.get("draft_prompt")
        if not isinstance(draft_prompt, str) or not draft_prompt.strip():
            fail(f"missing non-empty draft_prompt for {task_id}")
        by_id[task_id] = task

    successors: dict[str, list[str]] = defaultdict(list)
    indegree_all = {task_id: 0 for task_id in by_id}
    indegree_remaining = {task_id: 0 for task_id in by_id}
    seen_edges: set[tuple[str, str]] = set()
    for edge in edges:
        if not isinstance(edge, dict):
            fail("every dependency must be an object")
        source, target = edge.get("from"), edge.get("to")
        if source not in by_id or target not in by_id:
            fail(f"dependency references an unknown task: {source} -> {target}")
        if source == target:
            fail(f"self-dependency is not allowed: {source}")
        pair = (source, target)
        if pair in seen_edges:
            fail(f"duplicate dependency: {source} -> {target}")
        seen_edges.add(pair)
        successors[source].append(target)
        indegree_all[target] += 1
        if by_id[source].get("status", "planned") not in DONE:
            indegree_remaining[target] += 1

    queue = deque(sorted(task_id for task_id, degree in indegree_all.items() if degree == 0))
    visited = 0
    cycle_degrees = dict(indegree_all)
    while queue:
        task_id = queue.popleft()
        visited += 1
        for target in successors[task_id]:
            cycle_degrees[target] -= 1
            if cycle_degrees[target] == 0:
                queue.append(target)
    cyclic = sorted(task_id for task_id, degree in cycle_degrees.items() if degree > 0)

    ready = sorted(
        task_id
        for task_id, degree in indegree_remaining.items()
        if degree == 0 and by_id[task_id].get("status", "planned") in READY_STATUSES
    )
    ready_set = set(ready)
    ready_by_lane = {
        lane_id: sorted(task_id for task_id in ready if by_id[task_id]["lane"] == lane_id)
        for lane_id in sorted(lane_ids)
    }
    ready_collisions = []
    for collision in collisions:
        if not isinstance(collision, dict) or not isinstance(collision.get("tasks"), list):
            fail("every collision must be an object with a tasks array")
        task_ids = collision["tasks"]
        if len(task_ids) < 2 or any(task_id not in by_id for task_id in task_ids):
            fail(f"collision references invalid tasks: {task_ids}")
        if len(ready_set.intersection(task_ids)) >= 2:
            ready_collisions.append(collision)

    return {
        "valid_dag": not cyclic,
        "cyclic_tasks": cyclic,
        "completed": sorted(task_id for task_id, task in by_id.items() if task.get("status") in DONE),
        "indegree_remaining": indegree_remaining,
        "ready": ready if not cyclic else [],
        "ready_by_lane": ready_by_lane if not cyclic else {lane_id: [] for lane_id in sorted(lane_ids)},
        "ready_collisions": ready_collisions if not cyclic else [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path, help="path to plan JSON")
    args = parser.parse_args()
    try:
        result = analyze(load_plan(args.plan))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid_dag"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
