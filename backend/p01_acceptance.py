import argparse
import json
from pathlib import Path

from backend.experiment_matrix import build_matrix
from backend.experiment_results import build_summary
from backend.metrics_context_audit import build_metrics_context_audit
from backend.mobile_video_check import build_log_dir_report


def find_row(rows, case_id):
    return next((row for row in rows if row.get("id") == case_id or row.get("case_id") == case_id), None)


def check(label, ok, detail="", required=True):
    return {
        "label": label,
        "ok": bool(ok),
        "required": required,
        "detail": detail,
    }


def duration_ok(actual, target=5.0, tolerance=1.0):
    return actual is not None and abs(float(actual) - target) <= tolerance


def build_p01_acceptance(
    log_dir="logs",
    result_path="outputs/smoke-test/P01.mp4",
    p01_manifest_path="docs/p01-smoke-manifest.json",
    target_duration_seconds=5.0,
    duration_tolerance_seconds=1.0,
):
    matrix = build_matrix()
    summary_rows = build_summary(matrix, log_dir=log_dir)
    p01_summary = find_row(summary_rows, "P01") or {}

    context_audit = build_metrics_context_audit(log_dir=log_dir, p01_manifest_path=p01_manifest_path)
    p01_context = find_row(context_audit["rows"], "P01") or {}

    mobile_report = build_log_dir_report(log_dir=log_dir, case_ids=["P01"], matrix=matrix)
    p01_mobile = find_row(mobile_report["rows"], "P01") or {}

    result = Path(result_path)
    mobile_status = p01_mobile.get("status")
    mobile_ok = mobile_status in {"mobile_video_ready", "mobile_video_needs_transcode"}
    measured = p01_summary.get("status") == "measured"
    context_ready = p01_context.get("status") == "context_ready"
    result_exists = result.is_file()
    duration = p01_summary.get("video_duration_seconds")

    checks = [
        check("P01 runtime metrics measured", measured, p01_summary.get("metrics_path") or "missing metrics"),
        check("P01 metrics context ready", context_ready, p01_context.get("status") or "missing context"),
        check("P01 result mp4 exists", result_exists, str(result)),
        check(
            "P01 video duration near target",
            duration_ok(duration, target=target_duration_seconds, tolerance=duration_tolerance_seconds),
            "{} seconds, target {} +/- {}".format(duration, target_duration_seconds, duration_tolerance_seconds),
        ),
        check("P01 video has audio", p01_summary.get("has_audio") is True, str(p01_summary.get("has_audio"))),
        check("P01 video has video", p01_summary.get("has_video") is True, str(p01_summary.get("has_video"))),
        check("P01 mobile video evidence usable", mobile_ok, mobile_status or "missing mobile video evidence"),
    ]
    failures = [item for item in checks if item["required"] and not item["ok"]]
    if failures:
        status = "not_ready"
    elif mobile_status == "mobile_video_needs_transcode":
        status = "ready_for_full_suite_with_transcode_required"
    else:
        status = "ready_for_full_suite"

    return {
        "status": status,
        "log_dir": str(log_dir),
        "result_path": str(result_path),
        "p01_manifest_path": str(p01_manifest_path),
        "metrics_path": p01_summary.get("metrics_path"),
        "mobile_video_status": mobile_status,
        "checks": checks,
        "failures": failures,
        "summary": p01_summary,
        "context": p01_context,
        "mobile_video": p01_mobile,
    }


def markdown_p01_acceptance(report):
    lines = [
        "# P01 Smoke Acceptance",
        "",
        "- Status: `{}`".format(report["status"]),
        "- Metrics: {}".format(report.get("metrics_path") or "-"),
        "- Result: `{}`".format(report["result_path"]),
        "- Mobile video status: `{}`".format(report.get("mobile_video_status") or "missing"),
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for item in report["checks"]:
        lines.append(
            "| {label} | {status} | {detail} |".format(
                label=item["label"],
                status="ok" if item["ok"] else "failed",
                detail=item["detail"],
            )
        )
    if report["status"] == "ready_for_full_suite_with_transcode_required":
        lines.extend(
            [
                "",
                "P01 is sufficient to proceed with the full suite, but generated videos need a mobile delivery transcode path before final app feasibility can pass.",
            ]
        )
    elif report["status"] == "ready_for_full_suite":
        lines.extend(["", "P01 is sufficient to proceed with P03/P04/T01/T02."])
    else:
        lines.extend(["", "Do not proceed to the full suite until failed P01 checks are fixed."])
    return "\n".join(lines)


def write_output(text, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Decide whether P01 smoke evidence is sufficient to proceed to the full GPU suite")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--result-path", default="outputs/smoke-test/P01.mp4")
    parser.add_argument("--p01-manifest", default="docs/p01-smoke-manifest.json")
    parser.add_argument("--target-duration-seconds", type=float, default=5.0)
    parser.add_argument("--duration-tolerance-seconds", type=float, default=1.0)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero unless P01 is ready for the full suite.")
    args = parser.parse_args()

    report = build_p01_acceptance(
        log_dir=args.log_dir,
        result_path=args.result_path,
        p01_manifest_path=args.p01_manifest,
        target_duration_seconds=args.target_duration_seconds,
        duration_tolerance_seconds=args.duration_tolerance_seconds,
    )
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else markdown_p01_acceptance(report)
    if args.output:
        write_output(text, args.output)
    print(text)
    if args.strict and not report["status"].startswith("ready_for_full_suite"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
