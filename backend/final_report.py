import argparse
import json
from pathlib import Path

from backend.cost_review import build_cost_report, markdown_cost_report
from backend.experiment_results import build_report as build_runtime_report
from backend.feasibility_decision import build_decision, markdown_decision
from backend.quality_review import build_quality_report, markdown_quality_report


def report_status(decision):
    recommendation = decision["recommendation"]
    if recommendation == "B_pending_runtime":
        return "incomplete_runtime_evidence"
    if recommendation == "B_candidate_needs_quality_review":
        return "incomplete_quality_evidence"
    if recommendation == "B_candidate_needs_cost_review":
        return "incomplete_cost_evidence"
    if recommendation == "B_candidate_ready_for_product_review":
        return "cloud_candidate_ready_for_product_review"
    if recommendation.startswith("C_candidate"):
        return "stop_candidate"
    return "manual_review_required"


def evidence_gate_rows(decision):
    runtime = decision["runtime_evidence"]
    quality = decision["quality_evidence"]
    cost = decision["cost_evidence"]
    return [
        {
            "gate": "Static on-device feasibility",
            "status": decision["decisions"]["official_on_device"]["status"],
            "summary": "Official on-device stack is rejected by size, CUDA dependency, and missing mobile export path.",
        },
        {
            "gate": "Required GPU runtime metrics",
            "status": runtime["state"],
            "summary": runtime["summary"],
        },
        {
            "gate": "Generated sample quality",
            "status": quality["status"],
            "summary": quality["summary"],
        },
        {
            "gate": "Cloud GPU cost and wait time",
            "status": cost["status"],
            "summary": cost["summary"],
        },
    ]


def build_final_report(matrix_path=None, log_dir="logs", quality_review_path=None, cost_review_path=None):
    decision = build_decision(
        matrix_path=matrix_path,
        log_dir=log_dir,
        quality_review_path=quality_review_path,
        cost_review_path=cost_review_path,
    )
    runtime_report = build_runtime_report(matrix_path=matrix_path, log_dir=log_dir)
    quality_report = build_quality_report(quality_review_path)
    cost_report = build_cost_report(cost_review_path, matrix_path=matrix_path, log_dir=log_dir)
    return {
        "status": report_status(decision),
        "recommendation": decision["recommendation"],
        "evidence_gates": evidence_gate_rows(decision),
        "decision": decision,
        "runtime_report": runtime_report,
        "quality_report": quality_report,
        "cost_report": cost_report,
    }


def markdown_gate_table(rows):
    lines = [
        "| Gate | Status | Summary |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append("| {gate} | `{status}` | {summary} |".format(**row))
    return "\n".join(lines)


def demote_headings(text, levels=2):
    prefix = "#" * levels
    lines = []
    for line in text.splitlines():
        if line.startswith("#"):
            lines.append(prefix + line)
        else:
            lines.append(line)
    return "\n".join(lines)


def markdown_final_report(report):
    decision = report["decision"]
    lines = [
        "# Final Mobile Feasibility Report",
        "",
        "Status: `{}`".format(report["status"]),
        "",
        "Recommendation: `{}`".format(report["recommendation"]),
        "",
        "## Executive Summary",
        "",
        "- Official on-device inference is `{}`.".format(
            decision["decisions"]["official_on_device"]["status"]
        ),
        "- Cloud backend route is `{}`.".format(decision["decisions"]["cloud_backend"]["status"]),
        "- Stop/productization route is `{}`.".format(decision["decisions"]["stop_productization"]["status"]),
        "",
        "## Evidence Gates",
        "",
        markdown_gate_table(report["evidence_gates"]),
        "",
        "## Decision",
        "",
        demote_headings(markdown_decision(decision)),
        "",
        "## Runtime Metrics",
        "",
        report["runtime_report"]["markdown"],
        "",
        "## Quality Review",
        "",
        demote_headings(markdown_quality_report(report["quality_report"])),
        "",
        "## Cost Review",
        "",
        demote_headings(markdown_cost_report(report["cost_report"])),
    ]
    return "\n".join(lines)


def write_output(text, output):
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build a combined MagiHuman mobile feasibility report")
    parser.add_argument("--matrix")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--quality-review")
    parser.add_argument("--cost-review")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()

    report = build_final_report(
        matrix_path=args.matrix,
        log_dir=args.log_dir,
        quality_review_path=args.quality_review,
        cost_review_path=args.cost_review,
    )
    if args.format == "json":
        text = json.dumps(report, ensure_ascii=False, indent=2)
    else:
        text = markdown_final_report(report)
    if args.output:
        write_output(text, args.output)
    print(text)


if __name__ == "__main__":
    main()
