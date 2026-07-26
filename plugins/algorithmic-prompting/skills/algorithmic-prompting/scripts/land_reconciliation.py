#!/usr/bin/env python3
"""Land a human-reviewable reconciliation after every asynchronous view is ready."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from graph_ready import analyze, load_plan
from render_task_files import (
    MANIFEST_NAME,
    OVERVIEW_NAME,
    OVERVIEW_PLACEHOLDER_MARKER,
    PLACEHOLDER_MARKER,
    RECONCILIATION_NAME,
    RECONCILIATION_PLACEHOLDER_MARKER,
    atomic_write_text,
    bullet_list,
    load_manifest,
    one_line,
)


KINDS = {"task", "dependency", "collision"}
ACTIONS = {"confirm", "amend", "add", "remove", "merge", "split"}


def fail(message: str) -> None:
    raise ValueError(message)


def string_list(value: dict, field: str) -> list[str]:
    items = value.get(field, [])
    if not isinstance(items, list):
        fail(f"reconciliation result must contain an array for {field}")
    if any(not isinstance(item, str) or not item.strip() for item in items):
        fail(f"reconciliation result must contain only non-empty strings for {field}")
    return items


def load_reconciliation(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read reconciliation result: {exc}")
    if not isinstance(value, dict):
        fail("reconciliation result must be an object")
    summary = value.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        fail("reconciliation result must contain a non-empty summary")
    global_constraints = string_list(value, "global_constraints")
    human_decisions = string_list(value, "human_decisions")
    proposals = value.get("proposals", [])
    if not isinstance(proposals, list) or any(not isinstance(item, dict) for item in proposals):
        fail("reconciliation proposals must be an array of objects")
    for proposal in proposals:
        if proposal.get("kind") not in KINDS:
            fail(f"invalid reconciliation proposal kind: {proposal.get('kind')}")
        if proposal.get("action") not in ACTIONS:
            fail(f"invalid reconciliation proposal action: {proposal.get('action')}")
        targets = proposal.get("targets")
        if not isinstance(targets, list) or not targets or any(
            not isinstance(target, str) or not target.strip() for target in targets
        ):
            fail("every reconciliation proposal needs non-empty string targets")
        reason = proposal.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            fail("every reconciliation proposal needs a non-empty reason")
    return {
        "summary": summary,
        "global_constraints": global_constraints,
        "proposals": proposals,
        "human_decisions": human_decisions,
    }


def ensure_views_ready(output_dir: Path) -> None:
    overview_path = output_dir / OVERVIEW_NAME
    if not overview_path.exists() or OVERVIEW_PLACEHOLDER_MARKER in overview_path.read_text(
        encoding="utf-8"
    ):
        fail("system overview is not ready")
    if not (output_dir / ".system-overview.json").exists():
        fail("system-overview result is missing")

    manifest_path = output_dir / MANIFEST_NAME
    if not manifest_path.exists():
        fail("task manifest is missing")
    manifest = load_manifest(output_dir)
    if not manifest:
        fail("task manifest is empty")
    pending = [
        task_id
        for task_id, filename in manifest.items()
        if not (output_dir / filename).exists()
        or PLACEHOLDER_MARKER in (output_dir / filename).read_text(encoding="utf-8")
        or not (output_dir / ".task-details" / f"{task_id.lower()}.json").exists()
    ]
    if pending:
        fail(f"task details are not ready: {', '.join(sorted(pending))}")


def render_reconciliation(plan: dict, state: dict, result: dict) -> str:
    proposal_lines = [
        f"{item['kind']} · {item['action']} · {', '.join(item['targets'])} — {one_line(item['reason'])}"
        for item in result["proposals"]
    ]
    ready = ", ".join(state["ready"]) or "None"
    review_status = "human decision required" if result["proposals"] or result["human_decisions"] else "aligned"
    return f"""# Reconciliation — {one_line(plan.get('goal'), 'Task plan')}

- Status: {review_status}
- Current ready set: {ready}
- Graph mutation: not applied

## Summary

{one_line(result['summary'])}

## Global constraints

{bullet_list(result['global_constraints'])}

## Proposed graph changes

{bullet_list(proposal_lines)}

## Human decisions

{bullet_list(result['human_decisions'])}

Approve or reject proposed changes before updating the shared plan or advancing Kahn's algorithm.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path, help="path to the shared routing plan JSON")
    parser.add_argument("reconciliation", type=Path, help="path to the reconciliation JSON result")
    parser.add_argument("--output-dir", type=Path, required=True, help="planning artifact directory")
    args = parser.parse_args()

    try:
        plan = load_plan(args.plan)
        state = analyze(plan)
        if not state["valid_dag"]:
            fail("shared plan is cyclic")
        result = load_reconciliation(args.reconciliation)
        output_dir = args.output_dir.expanduser().resolve()
        ensure_views_ready(output_dir)
        reconciliation_path = output_dir / RECONCILIATION_NAME
        if not reconciliation_path.exists():
            fail("reconciliation placeholder is missing")
        if RECONCILIATION_PLACEHOLDER_MARKER not in reconciliation_path.read_text(
            encoding="utf-8"
        ):
            fail("reconciliation has already landed")

        result_path = output_dir / ".reconciliation.json"
        atomic_write_text(reconciliation_path, render_reconciliation(plan, state, result))
        atomic_write_text(result_path, json.dumps(result, indent=2, sort_keys=True) + "\n")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "status": "ready-for-human-review",
                "reconciliation_file": str(reconciliation_path),
                "reconciliation_result": str(result_path),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
