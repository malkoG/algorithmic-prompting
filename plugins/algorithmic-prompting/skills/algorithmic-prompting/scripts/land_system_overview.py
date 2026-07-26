#!/usr/bin/env python3
"""Atomically replace the system-overview placeholder with a broad, task-free scan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from graph_ready import analyze, load_plan
from render_task_files import (
    OVERVIEW_NAME,
    OVERVIEW_PLACEHOLDER_MARKER,
    atomic_write_text,
    bullet_list,
    one_line,
)


REQUIRED_ARRAYS = {
    "system_boundaries",
    "end_to_end_flows",
    "shared_invariants",
    "integration_surfaces",
}
OPTIONAL_ARRAYS = {"global_risks", "unknowns"}
DECOMPOSITION_FIELDS = {"tasks", "dependencies", "collisions", "lanes", "modules"}


def fail(message: str) -> None:
    raise ValueError(message)


def string_list(value: dict, field: str, *, required: bool) -> list[str]:
    items = value.get(field, [])
    if not isinstance(items, list):
        fail(f"overview result must contain an array for {field}")
    if any(not isinstance(item, str) or not item.strip() for item in items):
        fail(f"overview result must contain only non-empty strings for {field}")
    if required and not items:
        fail(f"overview result must contain at least one item for {field}")
    return items


def load_overview(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read overview result: {exc}")
    if not isinstance(value, dict):
        fail("overview result must be an object")
    summary = value.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        fail("overview result must contain a non-empty summary")
    forbidden = sorted(DECOMPOSITION_FIELDS.intersection(value))
    if forbidden:
        fail(f"overview result must not decompose work: {', '.join(forbidden)}")
    for field in REQUIRED_ARRAYS:
        string_list(value, field, required=True)
    for field in OPTIONAL_ARRAYS:
        string_list(value, field, required=False)
    return value


def render_overview(plan: dict, overview: dict) -> str:
    return f"""# System overview — {one_line(plan.get('goal'), 'Task plan')}

- Status: ready
- Scope: whole-system structure and behavior
- Task decomposition: excluded

## Summary

{one_line(overview['summary'])}

## System boundaries

{bullet_list(overview['system_boundaries'])}

## End-to-end flows

{bullet_list(overview['end_to_end_flows'])}

## Shared invariants

{bullet_list(overview['shared_invariants'])}

## Integration surfaces

{bullet_list(overview['integration_surfaces'])}

## Global risks

{bullet_list(overview.get('global_risks'))}

## Unknowns

{bullet_list(overview.get('unknowns'))}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path, help="path to the shared routing plan JSON")
    parser.add_argument("overview", type=Path, help="path to the overview-agent JSON result")
    parser.add_argument("--output-dir", type=Path, required=True, help="planning artifact directory")
    args = parser.parse_args()

    try:
        plan = load_plan(args.plan)
        state = analyze(plan)
        if not state["valid_dag"]:
            fail("shared plan is cyclic")
        overview = load_overview(args.overview)
        output_dir = args.output_dir.expanduser().resolve()
        overview_path = output_dir / OVERVIEW_NAME
        if not overview_path.exists():
            fail("system-overview placeholder is missing")
        if OVERVIEW_PLACEHOLDER_MARKER not in overview_path.read_text(encoding="utf-8"):
            fail("system overview has already landed")

        result_path = output_dir / ".system-overview.json"
        atomic_write_text(overview_path, render_overview(plan, overview))
        atomic_write_text(result_path, json.dumps(overview, indent=2, sort_keys=True) + "\n")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "status": "ready",
                "overview_file": str(overview_path),
                "overview_result": str(result_path),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
