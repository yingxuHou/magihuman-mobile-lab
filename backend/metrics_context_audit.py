import argparse
import json
from pathlib import Path

from backend.experiment_results import latest_metrics_path, load_matrix
from backend.run_metrics import sha256_file, sha256_text


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def as_number(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def values_match(expected, actual):
    expected_number = as_number(expected)
    actual_number = as_number(actual)
    if isinstance(expected_number, float) and isinstance(actual_number, float):
        return abs(expected_number - actual_number) < 1e-6
    return expected == actual


def check_field(name, expected, actual, required=True):
    if expected is None and actual is None and not required:
        ok = True
    elif required:
        ok = actual is not None and values_match(expected, actual)
    else:
        ok = actual is None or values_match(expected, actual)
    return {
        "field": name,
        "expected": expected,
        "actual": actual,
        "required": required,
        "ok": ok,
    }


def expected_context(case):
    profile = case["profile"]
    return {
        "case_id": case["id"],
        "mode": case["mode"],
        "resolution": case["resolution"],
        "variant": case["variant"],
        "seed": case["seed"],
        "target_duration_seconds": float(case["duration_seconds"]),
        "target_br_width": profile["br_width"],
        "target_br_height": profile["br_height"],
        "target_sr_width": profile.get("sr_width"),
        "target_sr_height": profile.get("sr_height"),
        "prompt_sha256": sha256_text(case["prompt"]),
    }


def expected_p01_manifest_context(manifest_path):
    manifest = load_json(manifest_path)
    actual = manifest["actual_p01_inputs"]
    return {
        "manifest_path": str(manifest_path).replace("\\", "/"),
        "manifest_sha256": sha256_file(manifest_path),
        "result_path": actual["expected_result_path"],
        "prompt_sha256": actual["prompt_sha256"],
        "seed": actual["seed"],
        "target_duration_seconds": float(actual["duration_seconds"]),
        "target_br_width": actual["base_width"],
        "target_br_height": actual["base_height"],
        "target_sr_width": actual.get("sr_width"),
        "target_sr_height": actual.get("sr_height"),
    }


def normalize_path(value):
    return str(value).replace("\\", "/") if value is not None else None


def audit_metrics_context(case, metrics_path, p01_manifest_path=None):
    if not metrics_path:
        return {
            "case_id": case["id"],
            "status": "missing_metrics",
            "metrics_path": None,
            "checks": [],
        }

    metrics = load_json(metrics_path)
    run = metrics.get("run") or {}
    if not run:
        return {
            "case_id": case["id"],
            "status": "missing_run_context",
            "metrics_path": str(metrics_path),
            "checks": [],
        }

    expected = expected_context(case)
    checks = [
        check_field("case_id", expected["case_id"], run.get("case_id")),
        check_field("mode", expected["mode"], run.get("mode")),
        check_field("resolution", expected["resolution"], run.get("resolution")),
        check_field("variant", expected["variant"], run.get("variant")),
        check_field("seed", expected["seed"], run.get("seed")),
        check_field("target_duration_seconds", expected["target_duration_seconds"], run.get("target_duration_seconds")),
        check_field("target_br_width", expected["target_br_width"], run.get("target_br_width")),
        check_field("target_br_height", expected["target_br_height"], run.get("target_br_height")),
        check_field("target_sr_width", expected["target_sr_width"], run.get("target_sr_width"), required=False),
        check_field("target_sr_height", expected["target_sr_height"], run.get("target_sr_height"), required=False),
        check_field("prompt_sha256", expected["prompt_sha256"], run.get("prompt_sha256")),
        check_field("result_path", "present", "present" if run.get("result_path") else None),
    ]

    if case["id"] == "P01" and p01_manifest_path and Path(p01_manifest_path).exists():
        manifest_expected = expected_p01_manifest_context(p01_manifest_path)
        checks.extend(
            [
                check_field("manifest_path", normalize_path(manifest_expected["manifest_path"]), normalize_path(run.get("manifest_path"))),
                check_field("manifest_sha256", manifest_expected["manifest_sha256"], run.get("manifest_sha256")),
                check_field("manifest_result_path", manifest_expected["result_path"], run.get("result_path")),
                check_field("manifest_seed", manifest_expected["seed"], run.get("seed")),
                check_field(
                    "manifest_target_duration_seconds",
                    manifest_expected["target_duration_seconds"],
                    run.get("target_duration_seconds"),
                ),
                check_field("manifest_target_br_width", manifest_expected["target_br_width"], run.get("target_br_width")),
                check_field("manifest_target_br_height", manifest_expected["target_br_height"], run.get("target_br_height")),
                check_field("manifest_prompt_sha256", manifest_expected["prompt_sha256"], run.get("prompt_sha256")),
            ]
        )

    failed = [check for check in checks if not check["ok"]]
    return {
        "case_id": case["id"],
        "status": "context_ready" if not failed else "context_mismatch",
        "metrics_path": str(metrics_path),
        "checks": checks,
        "failed_checks": failed,
    }


def build_metrics_context_audit(matrix_path=None, log_dir="logs", p01_manifest_path="docs/p01-smoke-manifest.json"):
    matrix = load_matrix(matrix_path)
    rows = []
    for case in matrix:
        metrics_path = latest_metrics_path(log_dir, case["id"])
        rows.append(audit_metrics_context(case, metrics_path, p01_manifest_path=p01_manifest_path))

    present_rows = [row for row in rows if row["status"] != "missing_metrics"]
    problem_rows = [row for row in present_rows if row["status"] != "context_ready"]
    if problem_rows:
        status = "context_not_ready"
    elif present_rows:
        status = "context_ready"
    else:
        status = "missing_metrics"

    return {
        "status": status,
        "log_dir": str(log_dir),
        "p01_manifest_path": str(p01_manifest_path) if p01_manifest_path else None,
        "rows": rows,
    }


def markdown_metrics_context_audit(audit):
    lines = [
        "# Metrics Context Audit",
        "",
        "Status: `{}`".format(audit["status"]),
        "",
        "| Case | Status | Metrics | Failed checks |",
        "| --- | --- | --- | --- |",
    ]
    for row in audit["rows"]:
        failed = row.get("failed_checks") or []
        failed_names = ", ".join(check["field"] for check in failed) if failed else "-"
        lines.append(
            "| {case} | `{status}` | {metrics} | {failed} |".format(
                case=row["case_id"],
                status=row["status"],
                metrics=row.get("metrics_path") or "-",
                failed=failed_names,
            )
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Audit run-context metadata in imported GPU metrics")
    parser.add_argument("--matrix")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--p01-manifest", default="docs/p01-smoke-manifest.json")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()

    audit = build_metrics_context_audit(
        matrix_path=args.matrix,
        log_dir=args.log_dir,
        p01_manifest_path=args.p01_manifest,
    )
    body = json.dumps(audit, ensure_ascii=False, indent=2) if args.format == "json" else markdown_metrics_context_audit(audit)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(body + "\n", encoding="utf-8")
    print(body)


if __name__ == "__main__":
    main()
