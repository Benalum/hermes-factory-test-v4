#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

SHA_HELP = "40-character lowercase git SHA"


def append_jsonl(path, record):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("evaluation_file")
    ap.add_argument("--project", required=True)
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--task-type", required=True)
    ap.add_argument("--role", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--provider")
    ap.add_argument("--selection-reason")

    ap.add_argument(
        "--success",
        action=argparse.BooleanOptionalAction,
        required=True,
    )

    ap.add_argument("--reviewer-score", type=float)
    ap.add_argument(
        "--required-rework",
        action=argparse.BooleanOptionalAction,
    )
    ap.add_argument(
        "--review-outcome",
        choices=["APPROVE", "REQUEST_CHANGES", "BLOCK"],
    )
    ap.add_argument(
        "--evidence-valid",
        action=argparse.BooleanOptionalAction,
    )

    ap.add_argument("--tests-total", type=int)
    ap.add_argument("--tests-passed", type=int)

    ap.add_argument("--attempts", type=int, default=1)
    ap.add_argument("--duration-seconds", type=float)
    ap.add_argument("--input-tokens", type=int)
    ap.add_argument("--output-tokens", type=int)
    ap.add_argument("--estimated-cost-usd", type=float)

    ap.add_argument(
        "--merged",
        action=argparse.BooleanOptionalAction,
    )
    ap.add_argument(
        "--delivery-valid",
        action=argparse.BooleanOptionalAction,
    )
    ap.add_argument("--status")

    ap.add_argument("--delivery-pr-url")
    ap.add_argument("--delivery-head-sha", help=SHA_HELP)
    ap.add_argument("--tested-sha", help=SHA_HELP)
    ap.add_argument("--reviewed-sha", help=SHA_HELP)
    ap.add_argument("--merged-sha", help=SHA_HELP)
    ap.add_argument("--ci-check")
    ap.add_argument(
        "--ci-passed",
        action=argparse.BooleanOptionalAction,
    )
    ap.add_argument(
        "--workspace-clean",
        action=argparse.BooleanOptionalAction,
    )
    ap.add_argument(
        "--pr-head-matched",
        action=argparse.BooleanOptionalAction,
    )
    ap.add_argument("--evidence", action="append", default=[])
    ap.add_argument("--notes")

    a = ap.parse_args()

    if a.reviewer_score is not None and not 0 <= a.reviewer_score <= 10:
        ap.error("--reviewer-score must be 0..10")

    if a.attempts < 1:
        ap.error("--attempts must be >= 1")

    for field in (
        "duration_seconds",
        "input_tokens",
        "output_tokens",
        "estimated_cost_usd",
        "tests_total",
        "tests_passed",
    ):
        value = getattr(a, field)
        if value is not None and value < 0:
            ap.error(f"--{field.replace('_', '-')} must be >= 0")

    if (
        a.tests_total is not None
        and a.tests_passed is not None
        and a.tests_passed > a.tests_total
    ):
        ap.error("--tests-passed cannot exceed --tests-total")

    for name in (
        "delivery_head_sha",
        "tested_sha",
        "reviewed_sha",
        "merged_sha",
    ):
        value = getattr(a, name)
        if value is not None and (
            len(value) != 40
            or any(c not in "0123456789abcdef" for c in value)
        ):
            ap.error(
                f"--{name.replace('_','-')} must be "
                "a 40-character lowercase git SHA"
            )

    software_evidence = any([
        a.delivery_pr_url,
        a.delivery_head_sha,
        a.tested_sha,
        a.reviewed_sha,
        a.merged_sha,
    ])

    if a.success and a.evidence_valid is not True:
        ap.error("--success requires --evidence-valid")

    if a.success and software_evidence:
        if a.delivery_valid is not True:
            ap.error(
                "successful software evaluation requires --delivery-valid"
            )
        if a.pr_head_matched is not True:
            ap.error(
                "successful software evaluation requires --pr-head-matched"
            )
        if a.ci_passed is not True:
            ap.error(
                "successful software evaluation requires --ci-passed"
            )

        candidate_shas = [
            a.delivery_head_sha,
            a.tested_sha,
            a.reviewed_sha,
        ]

        if any(v is None for v in candidate_shas):
            ap.error(
                "successful software evaluation requires "
                "delivery/tested/reviewed SHAs"
            )

        if len(set(candidate_shas)) != 1:
            ap.error(
                "delivery/tested/reviewed SHAs must match "
                "for successful software evaluation"
            )

    if a.merged is True and a.merged_sha is None:
        ap.error("--merged requires --merged-sha")

    if a.review_outcome == "APPROVE" and a.reviewed_sha is None:
        ap.error("APPROVE requires --reviewed-sha")

    if a.ci_passed is True and not a.ci_check:
        ap.error("--ci-passed requires --ci-check")

    rec = {
        "schema_version": 2,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": a.project,
        "task_id": a.task_id,
        "task_type": a.task_type,
        "role": a.role,
        "model": {
            "provider": a.provider,
            "name": a.model,
            "selection_reason": a.selection_reason,
        },
        "execution": {
            "attempts": a.attempts,
            "duration_seconds": a.duration_seconds,
            "input_tokens": a.input_tokens,
            "output_tokens": a.output_tokens,
            "estimated_cost_usd": a.estimated_cost_usd,
        },
        "evidence": {
            "delivery_pr_url": a.delivery_pr_url,
            "delivery_head_sha": a.delivery_head_sha,
            "tested_sha": a.tested_sha,
            "reviewed_sha": a.reviewed_sha,
            "merged_sha": a.merged_sha,
            "ci_check": a.ci_check,
            "ci_passed": a.ci_passed,
            "workspace_clean": a.workspace_clean,
            "pr_head_matched": a.pr_head_matched,
            "sources": list(a.evidence),
        },
        "verification": {
            "tests_total": a.tests_total,
            "tests_passed": a.tests_passed,
            "reviewer_score": a.reviewer_score,
            "required_rework": a.required_rework,
            "review_outcome": a.review_outcome,
            "evidence_valid": a.evidence_valid,
            "evidence": list(a.evidence),
        },
        "result": {
            "success": a.success,
            "merged": a.merged,
            "delivery_valid": a.delivery_valid,
            "status": a.status,
        },
        "notes": a.notes,
    }

    append_jsonl(a.evaluation_file, rec)

    print(
        f"Appended schema-v2 evaluation for {a.task_id} "
        f"using {a.provider or 'unknown-provider'}/{a.model}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
