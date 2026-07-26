#!/usr/bin/env python3
"""Atomically replace one task placeholder with its complete coding-agent prompt."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from graph_ready import PROMPT_PROFILES, analyze, load_plan
from render_task_files import atomic_write_text, load_manifest, render_task


LEGACY_ARRAY_FIELDS = {
    "context",
    "scope",
    "out_of_scope",
    "files",
    "acceptance_criteria",
    "validation",
    "proposed_dependencies",
    "proposed_collisions",
    "uncertainties",
}
LEGACY_STRING_FIELDS = {"completion_gate", "prompt_seed"}
TASK_FIELDS = {
    "context",
    "scope",
    "out_of_scope",
    "files",
    "acceptance_criteria",
    "validation",
    "completion_gate",
    "prompt_seed",
}


def fail(message: str) -> None:
    raise ValueError(message)


def string_list(value: dict, field: str, *, required: bool = False) -> list[str]:
    items = value.get(field, [])
    if not isinstance(items, list):
        fail(f"detail result must contain an array for {field}")
    if any(not isinstance(item, str) or not item.strip() for item in items):
        fail(f"detail result must contain only non-empty strings for {field}")
    if required and not items:
        fail(f"detail result must contain at least one item for {field}")
    return items


def load_detail(path: Path) -> tuple[dict, dict]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read detail result: {exc}")
    if not isinstance(value, dict):
        fail("detail result must be an object")
    task_id = value.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        fail("detail result must contain a non-empty task_id")
    profile = value.get("profile")
    if profile is not None and profile not in PROMPT_PROFILES:
        fail(f"invalid detail prompt profile: {profile}")

    compact = any(field in value for field in ("guidance", "done", "checks", "risks"))
    if compact:
        guidance = value.get("guidance")
        if not isinstance(guidance, str) or not guidance.strip():
            fail("compact detail result must contain non-empty guidance")
        scope = string_list(value, "scope", required=True)
        files = string_list(value, "files", required=True)
        done = string_list(value, "done", required=True)
        checks = string_list(value, "checks", required=True)
        context = string_list(value, "context")
        out_of_scope = string_list(value, "out_of_scope")
        risks = string_list(value, "risks")
        uncertainties = string_list(value, "uncertainties")
        proposed_dependencies = value.get("proposed_dependencies", [])
        proposed_collisions = value.get("proposed_collisions", [])
        completion_gate = value.get("completion_gate")
        if completion_gate is not None and (
            not isinstance(completion_gate, str) or not completion_gate.strip()
        ):
            fail("completion_gate must be a non-empty string when present")
        normalized = {
            "task_id": task_id,
            "context": context,
            "scope": scope,
            "out_of_scope": out_of_scope
            or ["Sibling task work", "Unrelated refactors or cleanup"],
            "files": files,
            "acceptance_criteria": done,
            "validation": checks,
            "completion_gate": completion_gate
            or "All acceptance criteria pass and focused checks succeed.",
            "prompt_seed": guidance,
            "risks": risks,
            "proposed_dependencies": proposed_dependencies,
            "proposed_collisions": proposed_collisions,
            "uncertainties": uncertainties,
        }
    else:
        for field in LEGACY_ARRAY_FIELDS:
            values = value.get(field)
            if not isinstance(values, list):
                fail(f"detail result must contain an array for {field}")
            optional = {"proposed_dependencies", "proposed_collisions", "uncertainties"}
            if field not in optional and (
                not values or any(not isinstance(item, str) or not item.strip() for item in values)
            ):
                fail(f"detail result must contain non-empty strings for {field}")
        for field in LEGACY_STRING_FIELDS:
            text = value.get(field)
            if not isinstance(text, str) or not text.strip():
                fail(f"detail result must contain a non-empty {field}")
        normalized = value

    if any(not isinstance(item, dict) for item in normalized["proposed_dependencies"]):
        fail("proposed_dependencies must contain objects")
    if any(not isinstance(item, dict) for item in normalized["proposed_collisions"]):
        fail("proposed_collisions must contain objects")
    if any(not isinstance(item, str) or not item.strip() for item in normalized["uncertainties"]):
        fail("uncertainties must contain non-empty strings")
    return value, normalized


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path, help="path to the shared plan JSON")
    parser.add_argument("detail", type=Path, help="path to one detail-agent JSON result")
    parser.add_argument("--output-dir", type=Path, required=True, help="placeholder task directory")
    args = parser.parse_args()

    try:
        plan = load_plan(args.plan)
        raw_detail, detail = load_detail(args.detail)
        state = analyze(plan)
        if not state["valid_dag"]:
            fail("shared plan is cyclic")

        task_id = detail["task_id"]
        tasks = {task["id"]: task for task in plan["tasks"]}
        if task_id not in tasks:
            fail(f"detail result references unknown task: {task_id}")

        output_dir = args.output_dir.expanduser().resolve()
        manifest = load_manifest(output_dir)
        if task_id not in manifest:
            fail(f"task is missing from the placeholder manifest: {task_id}")

        task = tasks[task_id]
        expected_profile = task.get("prompt_profile", plan.get("prompt_profile", "lean"))
        supplied_profile = raw_detail.get("profile")
        if supplied_profile is not None and supplied_profile != expected_profile:
            fail(
                f"detail profile {supplied_profile} does not match task profile {expected_profile}"
            )
        task["prompt_profile"] = expected_profile
        for field in TASK_FIELDS:
            if field == "context" and not detail[field]:
                continue
            task[field] = detail[field]
        task["detail_proposed_dependencies"] = detail["proposed_dependencies"]
        task["detail_proposed_collisions"] = detail["proposed_collisions"]
        task["detail_uncertainties"] = detail["uncertainties"]
        task["detail_risks"] = detail.get("risks", [])

        lanes = {lane["id"]: lane for lane in plan["lanes"]}
        content = render_task(
            plan,
            task,
            lanes[task["lane"]],
            plan.get("dependencies", []),
            plan.get("collisions", []),
            set(state["ready"]),
        )
        task_path = output_dir / manifest[task_id]
        detail_path = output_dir / ".task-details" / f"{task_id.lower()}.json"
        atomic_write_text(task_path, content)
        atomic_write_text(detail_path, json.dumps(raw_detail, indent=2, sort_keys=True) + "\n")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "task_id": task_id,
                "status": "ready",
                "task_file": str(task_path),
                "detail_result": str(detail_path),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
