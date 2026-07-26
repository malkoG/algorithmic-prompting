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
PROMPT_PROFILES = {"lean", "balanced", "thorough"}
TOPOLOGY_STATUSES = {"provisional", "reviewed"}
PLAN_STAGES = {"routing", "detailed"}


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
    modules = plan.get("modules", [])
    tasks = plan.get("tasks")
    edges = plan.get("dependencies", [])
    collisions = plan.get("collisions", [])
    if not isinstance(lanes, list) or not lanes:
        fail("lanes must be a non-empty array")
    if not isinstance(tasks, list) or not tasks:
        fail("tasks must be a non-empty array")
    if not isinstance(modules, list) or not isinstance(edges, list) or not isinstance(collisions, list):
        fail("modules, dependencies, and collisions must be arrays")
    plan_profile = plan.get("prompt_profile", "lean")
    if plan_profile not in PROMPT_PROFILES:
        fail(f"invalid prompt_profile: {plan_profile}")
    topology_status = plan.get("topology_status", "provisional")
    if topology_status not in TOPOLOGY_STATUSES:
        fail(f"invalid topology_status: {topology_status}")
    plan_stage = plan.get("plan_stage", "detailed")
    if plan_stage not in PLAN_STAGES:
        fail(f"invalid plan_stage: {plan_stage}")
    if plan_stage == "routing" and modules:
        fail("routing plans must defer modules to detail work")

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
        for field in ("paths",):
            values = lane.get(field)
            if not isinstance(values, list) or not values or any(not isinstance(value, str) or not value.strip() for value in values):
                fail(f"lane {lane_id} must have a non-empty string array for {field}")
        validation = lane.get("validation")
        if plan_stage == "detailed" and (
            not isinstance(validation, list)
            or not validation
            or any(not isinstance(value, str) or not value.strip() for value in validation)
        ):
            fail(f"lane {lane_id} must have a non-empty string array for validation")
        if validation is not None and (
            not isinstance(validation, list)
            or any(not isinstance(value, str) or not value.strip() for value in validation)
        ):
            fail(f"lane {lane_id} validation must contain only non-empty strings")
        lane_ids.add(lane_id)

    modules_by_id: dict[str, dict] = {}
    for module in modules:
        if not isinstance(module, dict) or not isinstance(module.get("id"), str):
            fail("every module must be an object with a string id")
        module_id = module["id"]
        if not re.fullmatch(r"[A-Z][A-Z0-9-]*", module_id):
            fail(f"invalid module id: {module_id}")
        if module_id in modules_by_id:
            fail(f"duplicate module id: {module_id}")
        if module.get("lane") not in lane_ids:
            fail(f"unknown or missing lane for module {module_id}: {module.get('lane')}")
        if module.get("status", "planned") not in VALID_STATUSES:
            fail(f"invalid status for module {module_id}: {module.get('status')}")
        for field in ("input", "output"):
            if not isinstance(module.get(field), str) or not module[field].strip():
                fail(f"module {module_id} must have a non-empty {field}")
        for field in ("owns", "validation"):
            values = module.get(field)
            if not isinstance(values, list) or not values or any(
                not isinstance(value, str) or not value.strip() for value in values
            ):
                fail(f"module {module_id} must have a non-empty string array for {field}")
        modules_by_id[module_id] = module

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
        if modules_by_id:
            module_id = task.get("module")
            if module_id not in modules_by_id:
                fail(f"unknown or missing module for {task_id}: {module_id}")
            if modules_by_id[module_id]["lane"] != lane_id:
                fail(f"task {task_id} lane must match module {module_id} lane")
        status = task.get("status", "planned")
        if status not in VALID_STATUSES:
            fail(f"invalid status for {task_id}: {status}")
        if not isinstance(task.get("title"), str) or not task["title"].strip():
            fail(f"missing non-empty title for {task_id}")
        task_profile = task.get("prompt_profile", plan_profile)
        if task_profile not in PROMPT_PROFILES:
            fail(f"invalid prompt_profile for {task_id}: {task_profile}")
        prompt_seed = task.get("prompt_seed", task.get("draft_prompt"))
        if plan_stage == "detailed" and (
            not isinstance(prompt_seed, str) or not prompt_seed.strip()
        ):
            fail(f"missing non-empty prompt_seed for {task_id}")
        if prompt_seed is not None and (
            not isinstance(prompt_seed, str) or not prompt_seed.strip()
        ):
            fail(f"prompt_seed for {task_id} must be a non-empty string when present")
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

    tasks_by_lane: dict[str, list[str]] = defaultdict(list)
    for task_id, task in by_id.items():
        tasks_by_lane[task["lane"]].append(task_id)
    lane_completed = {
        lane_id
        for lane_id in lane_ids
        if tasks_by_lane[lane_id]
        and all(by_id[task_id].get("status", "planned") in DONE for task_id in tasks_by_lane[lane_id])
    }
    lane_dependencies: dict[tuple[str, str], dict] = {}
    lane_successors: dict[str, list[str]] = defaultdict(list)
    lane_indegree_all = {lane_id: 0 for lane_id in lane_ids}
    lane_indegree_remaining = {lane_id: 0 for lane_id in lane_ids}
    for edge in edges:
        source_lane = by_id[edge["from"]]["lane"]
        target_lane = by_id[edge["to"]]["lane"]
        if source_lane == target_lane:
            continue
        pair = (source_lane, target_lane)
        detail = lane_dependencies.setdefault(
            pair,
            {"from": source_lane, "to": target_lane, "task_edges": [], "reasons": []},
        )
        detail["task_edges"].append(f"{edge['from']} -> {edge['to']}")
        reason = edge.get("reason")
        if isinstance(reason, str) and reason.strip() and reason not in detail["reasons"]:
            detail["reasons"].append(reason)
    for source_lane, target_lane in sorted(lane_dependencies):
        lane_successors[source_lane].append(target_lane)
        lane_indegree_all[target_lane] += 1
        if source_lane not in lane_completed:
            lane_indegree_remaining[target_lane] += 1
    lane_queue = deque(sorted(lane_id for lane_id, degree in lane_indegree_all.items() if degree == 0))
    lane_cycle_degrees = dict(lane_indegree_all)
    while lane_queue:
        lane_id = lane_queue.popleft()
        for target in lane_successors[lane_id]:
            lane_cycle_degrees[target] -= 1
            if lane_cycle_degrees[target] == 0:
                lane_queue.append(target)
    cyclic_lanes = sorted(lane_id for lane_id, degree in lane_cycle_degrees.items() if degree > 0)
    lane_ready = sorted(
        lane_id
        for lane_id, degree in lane_indegree_remaining.items()
        if degree == 0 and lane_id not in lane_completed and ready_by_lane[lane_id]
    )

    module_dependencies: dict[tuple[str, str], dict] = {}
    module_successors: dict[str, list[str]] = defaultdict(list)
    module_indegree_all = {module_id: 0 for module_id in modules_by_id}
    module_indegree_remaining = {module_id: 0 for module_id in modules_by_id}
    tasks_by_module: dict[str, list[str]] = defaultdict(list)
    for task_id, task in by_id.items():
        if task.get("module"):
            tasks_by_module[task["module"]].append(task_id)

    module_completed = {
        module_id
        for module_id, module in modules_by_id.items()
        if module.get("status") in DONE
        or (
            tasks_by_module[module_id]
            and all(by_id[task_id].get("status", "planned") in DONE for task_id in tasks_by_module[module_id])
        )
    }
    for edge in edges:
        source_module = by_id[edge["from"]].get("module")
        target_module = by_id[edge["to"]].get("module")
        if not source_module or not target_module or source_module == target_module:
            continue
        pair = (source_module, target_module)
        detail = module_dependencies.setdefault(
            pair,
            {"from": source_module, "to": target_module, "task_edges": [], "reasons": []},
        )
        detail["task_edges"].append(f"{edge['from']} -> {edge['to']}")
        reason = edge.get("reason")
        if isinstance(reason, str) and reason.strip() and reason not in detail["reasons"]:
            detail["reasons"].append(reason)

    for source_module, target_module in sorted(module_dependencies):
        module_successors[source_module].append(target_module)
        module_indegree_all[target_module] += 1
        if source_module not in module_completed:
            module_indegree_remaining[target_module] += 1

    module_queue = deque(sorted(module_id for module_id, degree in module_indegree_all.items() if degree == 0))
    module_cycle_degrees = dict(module_indegree_all)
    while module_queue:
        module_id = module_queue.popleft()
        for target in module_successors[module_id]:
            module_cycle_degrees[target] -= 1
            if module_cycle_degrees[target] == 0:
                module_queue.append(target)
    cyclic_modules = sorted(module_id for module_id, degree in module_cycle_degrees.items() if degree > 0)

    ready_by_module = {
        module_id: sorted(task_id for task_id in ready if by_id[task_id].get("module") == module_id)
        for module_id in sorted(modules_by_id)
    }
    module_ready = sorted(
        module_id
        for module_id, degree in module_indegree_remaining.items()
        if degree == 0
        and module_id not in module_completed
        and modules_by_id[module_id].get("status", "planned") in READY_STATUSES
        and ready_by_module[module_id]
    )
    valid_dag = not cyclic and not cyclic_lanes and not cyclic_modules

    return {
        "valid_dag": valid_dag,
        "cyclic_tasks": cyclic,
        "valid_lane_dag": not cyclic_lanes,
        "cyclic_lanes": cyclic_lanes,
        "lane_dependencies": [lane_dependencies[pair] for pair in sorted(lane_dependencies)],
        "lane_completed": sorted(lane_completed),
        "lane_indegree_remaining": lane_indegree_remaining,
        "lane_ready": lane_ready if valid_dag else [],
        "valid_module_dag": not cyclic_modules,
        "cyclic_modules": cyclic_modules,
        "completed": sorted(task_id for task_id, task in by_id.items() if task.get("status") in DONE),
        "indegree_remaining": indegree_remaining,
        "ready": ready if valid_dag else [],
        "ready_by_lane": ready_by_lane if valid_dag else {lane_id: [] for lane_id in sorted(lane_ids)},
        "ready_collisions": ready_collisions if valid_dag else [],
        "module_dependencies": [module_dependencies[pair] for pair in sorted(module_dependencies)],
        "module_completed": sorted(module_completed),
        "module_indegree_remaining": module_indegree_remaining,
        "module_ready": module_ready if valid_dag else [],
        "ready_by_module": ready_by_module if valid_dag else {module_id: [] for module_id in sorted(modules_by_id)},
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
