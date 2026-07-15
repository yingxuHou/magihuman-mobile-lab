import argparse
import json
from pathlib import Path

from backend.experiment_matrix import build_matrix
from backend.experiment_results import build_summary
from backend.experiment_suite import REQUIRED_CASE_IDS
from backend.metrics_context_audit import build_metrics_context_audit
from backend.mobile_video_check import build_log_dir_report


def find_case(matrix, case_id):
    return next((case for case in matrix if case["id"] == case_id), None)


def find_row(rows, case_id):
    return next((row for row in rows if row.get("id") == case_id or row.get("case_id") == case_id), None)


def check(label, ok, detail="", required=True):
    return {
        "label": label,
        "ok": bool(ok),
        "required": required,
        "detail": detail,
    }


def duration_ok(actual, target, tolerance):
    return actual is not None and abs(float(actual) - float(target)) <= tolerance


def result_path_for_case(case_id, result_dir, p01_result_path):
    if case_id == "P01":
        return Path(p01_result_path)
    return Path(result_dir) / "{}.mp4".format(case_id)


def build_case_acceptance(case, summary_row, context_row, mobile_row, result_path, duration_tolerance_seconds):
    summary_row = summary_row or {}
    context_row = context_row or {}
    mobile_row = mobile_row or {}
    mobile_status = mobile_row.get("status")
    mobile_ok = mobile_status in {"mobile_video_ready", "mobile_video_needs_transcode"}
    duration = summary_row.get("video_duration_seconds")
    result = Path(result_path)

    checks = [
        check("runtime metrics measured", summary_row.get("status") == "measured", summary_row.get("metrics_path") or "missing metrics"),
        check("metrics context ready", context_row.get("status") == "context_ready", context_row.get("status") or "missing context"),
        check("result mp4 exists", result.is_file(), str(result)),
        check(
            "video duration near target",
            duration_ok(duration, case["duration_seconds"], duration_tolerance_seconds),
            "{} seconds, target {} +/- {}".format(duration, case["duration_seconds"], duration_tolerance_seconds),
        ),
        check("video has audio", summary_row.get("has_audio") is True, str(summary_row.get("has_audio"))),
        check("video has video", summary_row.get("has_video") is True, str(summary_row.get("has_video"))),
        check("mobile video evidence usable", mobile_ok, mobile_status or "missing mobile video evidence"),
    ]
    failures = [item for item in checks if item["required"] and not item["ok"]]
    return {
        "case_id": case["id"],
        "status": "ready" if not failures else "not_ready",
        "metrics_path": summary_row.get("metrics_path"),
        "result_path": str(result),
        "mobile_video_status": mobile_status,
        "checks": checks,
        "failures": failures,
        "summary": summary_row,
        "context": context_row,
        "mobile_video": mobile_row,
    }


def build_required_suite_acceptance(
    log_dir="logs",
    result_dir="outputs/experiment-results",
    p01_result_path="outputs/smoke-test/P01.mp4",
    p01_manifest_path="docs/p01-smoke-manifest.json",
    case_ids=None,
    duration_tolerance_seconds=1.0,
):
    case_ids = list(case_ids or REQUIRED_CASE_IDS)
    matrix = build_matrix()
    summary_rows = build_summary(matrix, log_dir=log_dir)
    context_audit = build_metrics_context_audit(log_dir=log_dir, p01_manifest_path=p01_manifest_path)
    mobile_report = build_log_dir_report(log_dir=log_dir, case_ids=case_ids, matrix=matrix)

    rows = []
    for case_id in case_ids:
        case = find_case(matrix, case_id)
        if not case:
            rows.append(
                {
                    "case_id": case_id,
                    "status": "not_ready",
                    "metrics_path": None,
                    "result_path": None,
                    "mobile_video_status": None,
                    "checks": [check("known experiment case", False, "unknown case id")],
                    "failures": [check("known experiment case", False, "unknown case id")],
                    "summary": {},
                    "context": {},
                    "mobile_video": {},
                }
            )
            continue
        rows.append(
            build_case_acceptance(
                case,
                find_row(summary_rows, case_id),
                find_row(context_audit["rows"], case_id),
                find_row(mobile_report["rows"], case_id),
                result_path_for_case(case_id, result_dir, p01_result_path),
                duration_tolerance_seconds,
            )
        )

    failures = [failure for row in rows for failure in row["failures"]]
    if failures:
        status = "not_ready"
    elif any(row["mobile_video_status"] == "mobile_video_needs_transcode" for row in rows):
        status = "ready_for_quality_and_cost_review_with_transcode_required"
    else:
        status = "ready_for_quality_and_cost_review"

    return {
        "status": status,
        "log_dir": str(log_dir),
        "result_dir": str(result_dir),
        "p01_result_path": str(p01_result_path),
        "p01_manifest_path": str(p01_manifest_path),
        "case_ids": case_ids,
        "rows": rows,
        "failures": failures,
        "metrics_context_status": context_audit["status"],
        "mobile_video_status": mobile_report["status"],
    }


def markdown_required_suite_acceptance(report):
    lines = [
        "# Required Suite Acceptance",
        "",
        "- Status: `{}`".format(report["status"]),
        "- Cases: {}".format(", ".join(report["case_ids"])),
        "- Metrics context status: `{}`".format(report["metrics_context_status"]),
        "- Mobile video status: `{}`".format(report["mobile_video_status"]),
        "",
        "| Case | Status | Metrics | Result | Mobile video | Failed checks |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["rows"]:
        failures = ", ".join(item["label"] for item in row["failures"]) or "-"
        lines.append(
            "| {case} | `{status}` | {metrics} | `{result}` | `{mobile}` | {failures} |".format(
                case=row["case_id"],
                status=row["status"],
                metrics=row.get("metrics_path") or "-",
                result=row.get("result_path") or "-",
                mobile=row.get("mobile_video_status") or "missing",
                failures=failures,
            )
        )
    if report["status"] == "ready_for_quality_and_cost_review_with_transcode_required":
        lines.extend(
            [
                "",
                "Runtime evidence is sufficient to proceed to quality and cost review, but final mobile delivery still needs a transcode path.",
            ]
        )
    elif report["status"] == "ready_for_quality_and_cost_review":
        lines.extend(["", "Runtime evidence is sufficient to proceed to quality and cost review."])
    else:
        lines.extend(["", "Do not use this run for final App feasibility until failed checks are fixed."])
    return "\n".join(lines)


def write_output(text, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Decide whether the required MagiHuman GPU suite is ready for final reviews")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--result-dir", default="outputs/experiment-results")
    parser.add_argument("--p01-result-path", default="outputs/smoke-test/P01.mp4")
    parser.add_argument("--p01-manifest", default="docs/p01-smoke-manifest.json")
    parser.add_argument("--cases", nargs="+")
    parser.add_argument("--duration-tolerance-seconds", type=float, default=1.0)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero unless the required suite is ready for reviews.")
    args = parser.parse_args()

    report = build_required_suite_acceptance(
        log_dir=args.log_dir,
        result_dir=args.result_dir,
        p01_result_path=args.p01_result_path,
        p01_manifest_path=args.p01_manifest,
        case_ids=args.cases,
        duration_tolerance_seconds=args.duration_tolerance_seconds,
    )
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else markdown_required_suite_acceptance(report)
    if args.output:
        write_output(text, args.output)
    print(text)
    if args.strict and not report["status"].startswith("ready_for_quality_and_cost_review"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
