import argparse
import json
from pathlib import Path

from backend.final_report import build_final_report, demote_headings, markdown_final_report


COMPLETE_REPORT_STATUSES = {
    "cloud_candidate_ready_for_product_review",
    "mobile_video_needs_transcode",
    "stop_candidate",
}


def artifact_path(path):
    return str(Path(path)) if path else None


def gate_statuses(final_report):
    return {row["gate"]: row["status"] for row in final_report["evidence_gates"]}


def missing_evidence(final_report):
    decision = final_report["decision"]
    missing = []

    runtime_missing = decision["runtime_evidence"]["missing_required_case_ids"]
    if runtime_missing:
        missing.append(
            {
                "gate": "runtime",
                "items": runtime_missing,
                "action": "Import logs/*_metrics.json from the GPU host for the missing cases.",
            }
        )

    quality_status = decision["quality_evidence"]["status"]
    if quality_status in ("missing_quality_review", "incomplete_quality_review"):
        missing.append(
            {
                "gate": "quality",
                "items": [quality_status],
                "action": "Import or complete docs/quality-review.json.",
            }
        )

    cost_status = decision["cost_evidence"]["status"]
    if cost_status in ("missing_cost_review", "incomplete_cost_review"):
        missing.append(
            {
                "gate": "cost",
                "items": [cost_status],
                "action": "Import or complete docs/cost-review.json.",
            }
        )

    mobile_video = final_report.get("mobile_video_report", {})
    mobile_status = mobile_video.get("status")
    if mobile_status == "missing_mobile_video_evidence":
        missing_cases = [
            row["case_id"]
            for row in mobile_video.get("rows", [])
            if row.get("status") == "missing_video_metrics"
        ]
        missing.append(
            {
                "gate": "mobile_video",
                "items": missing_cases or [mobile_status],
                "action": "Import metrics JSON with ffprobe video metadata for generated samples.",
            }
        )
    elif mobile_status == "mobile_video_not_ready":
        failed_cases = [
            row["case_id"]
            for row in mobile_video.get("rows", [])
            if row.get("status") == "mobile_video_not_ready"
        ]
        missing.append(
            {
                "gate": "mobile_video",
                "items": failed_cases or [mobile_status],
                "action": "Review generated videos and produce mobile-compatible delivery files or record why app playback is not viable.",
            }
        )

    return missing


def build_import_audit(
    matrix_path=None,
    log_dir="logs",
    quality_review_path=None,
    cost_review_path=None,
    final_report_output=None,
):
    final_report = build_final_report(
        matrix_path=matrix_path,
        log_dir=log_dir,
        quality_review_path=quality_review_path,
        cost_review_path=cost_review_path,
    )
    missing = missing_evidence(final_report)
    status = "ready_for_final_update" if final_report["status"] in COMPLETE_REPORT_STATUSES else "incomplete_import"
    if missing:
        status = "incomplete_import"

    return {
        "status": status,
        "final_report_status": final_report["status"],
        "recommendation": final_report["recommendation"],
        "paths": {
            "log_dir": artifact_path(log_dir),
            "quality_review": artifact_path(quality_review_path),
            "cost_review": artifact_path(cost_review_path),
            "final_report_output": artifact_path(final_report_output),
        },
        "gate_statuses": gate_statuses(final_report),
        "missing_evidence": missing,
        "final_report": final_report,
    }


def markdown_import_audit(audit):
    lines = [
        "# GPU Evidence Import Audit",
        "",
        "Status: `{}`".format(audit["status"]),
        "",
        "Final report status: `{}`".format(audit["final_report_status"]),
        "",
        "Recommendation: `{}`".format(audit["recommendation"]),
        "",
        "## Inputs",
        "",
        "| Input | Path |",
        "| --- | --- |",
    ]
    for name, path in audit["paths"].items():
        lines.append("| {} | {} |".format(name, path or "-"))

    lines.extend(
        [
            "",
            "## Gate Statuses",
            "",
            "| Gate | Status |",
            "| --- | --- |",
        ]
    )
    for gate, status in audit["gate_statuses"].items():
        lines.append("| {} | `{}` |".format(gate, status))

    lines.extend(
        [
            "",
            "## Missing Evidence",
            "",
            "| Gate | Items | Action |",
            "| --- | --- | --- |",
        ]
    )
    if not audit["missing_evidence"]:
        lines.append("| - | - | Evidence package is complete enough to regenerate the final report. |")
    else:
        for item in audit["missing_evidence"]:
            lines.append("| {gate} | {items} | {action} |".format(
                gate=item["gate"],
                items=", ".join(item["items"]),
                action=item["action"],
            ))

    lines.extend(
        [
            "",
            "## Current Final Report",
            "",
            demote_headings(markdown_final_report(audit["final_report"])),
        ]
    )
    return "\n".join(lines)


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Audit imported GPU evidence before updating the final report")
    parser.add_argument("--matrix")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--quality-review")
    parser.add_argument("--cost-review")
    parser.add_argument("--final-report-output")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()

    audit = build_import_audit(
        matrix_path=args.matrix,
        log_dir=args.log_dir,
        quality_review_path=args.quality_review,
        cost_review_path=args.cost_review,
        final_report_output=args.final_report_output,
    )
    body = json.dumps(audit, ensure_ascii=False, indent=2) if args.format == "json" else markdown_import_audit(audit)
    if args.output:
        write_text(args.output, body)
    print(body)


if __name__ == "__main__":
    main()
