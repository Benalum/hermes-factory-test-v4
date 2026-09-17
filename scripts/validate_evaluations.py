#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


def typename(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def type_matches(value, expected):
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
        )
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    return False


def validate_schema(value, schema, path="$"):
    errors = []

    expected = schema.get("type")
    if expected is not None:
        allowed = expected if isinstance(expected, list) else [expected]
        if not any(type_matches(value, t) for t in allowed):
            return [
                f"{path}: expected type {allowed}, got {typename(value)}"
            ]

    if "const" in schema and value != schema["const"]:
        errors.append(
            f"{path}: expected constant {schema['const']!r}, "
            f"got {value!r}"
        )

    if "enum" in schema and value not in schema["enum"]:
        errors.append(
            f"{path}: value {value!r} not in enum {schema['enum']!r}"
        )

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(
                f"{path}: string shorter than {schema['minLength']}"
            )
        if "pattern" in schema:
            if re.search(schema["pattern"], value) is None:
                errors.append(
                    f"{path}: value does not match {schema['pattern']!r}"
                )

    if (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
    ):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(
                f"{path}: {value} is below minimum {schema['minimum']}"
            )
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(
                f"{path}: {value} exceeds maximum {schema['maximum']}"
            )

    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            errors.extend(
                validate_schema(
                    item,
                    schema["items"],
                    f"{path}[{i}]",
                )
            )

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{path}: missing required property {key!r}")

        properties = schema.get("properties", {})
        for key, child in value.items():
            if key in properties:
                errors.extend(
                    validate_schema(
                        child,
                        properties[key],
                        f"{path}.{key}",
                    )
                )
            elif schema.get("additionalProperties") is False:
                errors.append(
                    f"{path}: unexpected property {key!r}"
                )

    return errors


def semantic_errors(rec):
    errors = []

    evidence = rec.get("evidence")
    verification = rec.get("verification")
    result = rec.get("result")

    if not isinstance(evidence, dict):
        return ["evidence object is required"]

    if not isinstance(verification, dict):
        return ["verification object is required"]

    if not isinstance(result, dict):
        return ["result object is required"]

    delivery_sha = evidence.get("delivery_head_sha")
    tested_sha = evidence.get("tested_sha")
    reviewed_sha = evidence.get("reviewed_sha")
    merged_sha = evidence.get("merged_sha")

    if result.get("merged") is True and not merged_sha:
        errors.append("result.merged=true requires evidence.merged_sha")

    if evidence.get("ci_passed") is True and not evidence.get("ci_check"):
        errors.append(
            "evidence.ci_passed=true requires evidence.ci_check"
        )

    if (
        verification.get("review_outcome") == "APPROVE"
        and not reviewed_sha
    ):
        errors.append(
            "review_outcome=APPROVE requires evidence.reviewed_sha"
        )

    total = verification.get("tests_total")
    passed = verification.get("tests_passed")

    if (
        total is not None
        and passed is not None
        and passed > total
    ):
        errors.append(
            "verification.tests_passed cannot exceed tests_total"
        )

    software_evidence = any([
        evidence.get("delivery_pr_url"),
        delivery_sha,
        tested_sha,
        reviewed_sha,
        merged_sha,
    ])

    if result.get("success") is True:
        if verification.get("evidence_valid") is not True:
            errors.append(
                "result.success=true requires "
                "verification.evidence_valid=true"
            )

        if software_evidence:
            if result.get("delivery_valid") is not True:
                errors.append(
                    "successful software evaluation requires "
                    "result.delivery_valid=true"
                )

            if evidence.get("pr_head_matched") is not True:
                errors.append(
                    "successful software evaluation requires "
                    "evidence.pr_head_matched=true"
                )

            if evidence.get("ci_passed") is not True:
                errors.append(
                    "successful software evaluation requires "
                    "evidence.ci_passed=true"
                )

            candidate = [
                delivery_sha,
                tested_sha,
                reviewed_sha,
            ]

            if any(v is None for v in candidate):
                errors.append(
                    "successful software evaluation requires "
                    "delivery/tested/reviewed SHAs"
                )
            elif len(set(candidate)) != 1:
                errors.append(
                    "delivery/tested/reviewed SHAs must match "
                    "for successful software evaluation"
                )

    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("evaluation_file")
    ap.add_argument(
        "--schema",
        default="schemas/evaluation.schema.json",
    )
    ap.add_argument(
        "--require-records",
        action="store_true",
        help="fail if the JSONL file contains no nonblank records",
    )
    args = ap.parse_args()

    schema_path = Path(args.schema)
    evaluation_path = Path(args.evaluation_file)

    try:
        schema = json.loads(schema_path.read_text())
    except Exception as exc:
        print(f"ERROR: cannot load schema: {exc}", file=sys.stderr)
        return 2

    if not evaluation_path.exists():
        print(
            f"ERROR: evaluation file does not exist: "
            f"{evaluation_path}",
            file=sys.stderr,
        )
        return 2

    raw_lines = evaluation_path.read_text().splitlines()

    if args.require_records and not any(
        line.strip() for line in raw_lines
    ):
        print(
            "EVALUATION VALIDATION FAIL: no evaluation records",
            file=sys.stderr,
        )
        return 1

    failures = 0
    records = 0

    for lineno, raw in enumerate(
        raw_lines,
        start=1,
    ):
        if not raw.strip():
            continue

        records += 1

        try:
            rec = json.loads(raw)
        except json.JSONDecodeError as exc:
            failures += 1
            print(
                f"ERROR line {lineno}: invalid JSON: {exc}",
                file=sys.stderr,
            )
            continue

        errs = validate_schema(rec, schema)
        errs.extend(semantic_errors(rec))

        if errs:
            failures += 1
            for err in errs:
                print(
                    f"ERROR line {lineno}: {err}",
                    file=sys.stderr,
                )

    if failures:
        print(
            f"EVALUATION VALIDATION FAIL: "
            f"{failures} invalid record(s)",
            file=sys.stderr,
        )
        return 1

    print(
        f"EVALUATION VALIDATION PASS: {records} record(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
