import argparse
import json
from pathlib import Path

from backend.final_report import build_final_report
from backend.gpu_execution_packet import build_execution_packet
from backend.required_suite_acceptance import build_required_suite_acceptance
from backend.review_readiness import build_review_readiness


FINAL_READY_STATUSES = {
    "cloud_candidate_ready_for_product_review",
    "stop_candidate",
}


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")


def gate_statuses(final_report):
    return {row["gate"]: row["status"] for row in final_report["evidence_gates"]}


def missing_runtime_cases(final_report):
    return final_report["decision"]["runtime_evidence"]["missing_required_case_ids"]


def missing_mobile_cases(final_report):
    return [
        row["case_id"]
        for row in final_report["mobile_video_report"].get("rows", [])
        if row.get("status") == "missing_video_metrics"
    ]


def build_gap_items(final_report, required_suite_acceptance, review_readiness, execution_packet):
    gaps = []
    runtime_missing = missing_runtime_cases(final_report)
    if runtime_missing:
        gaps.append(
            {
                "gate": "Required GPU runtime metrics",
                "status": "missing",
                "detail": "Missing required cases: {}".format(", ".join(runtime_missing)),
                "next_action": "Run the GPU execution packet on a Linux NVIDIA GPU host and import the returned evidence package.",
            }
        )

    if required_suite_acceptance["status"] == "not_ready":
        gaps.append(
            {
                "gate": "Required-suite acceptance",
                "status": "not_ready",
                "detail": "Runtime, context, result MP4, duration, audio/video, or mobile playback checks are not complete.",
                "next_action": "Use `python -m backend.required_suite_acceptance --format markdown` after GPU evidence import.",
            }
        )

    mobile_missing = missing_mobile_cases(final_report)
    if mobile_missing:
        gaps.append(
            {
                "gate": "Mobile video playback evidence",
                "status": "missing",
                "detail": "Missing mobile playback metrics for: {}".format(", ".join(mobile_missing)),
                "next_action": "Collect ffprobe/video metadata from generated MP4 outputs and rerun mobile video checks.",
            }
        )

    if final_report["quality_report"]["status"] in {"missing_quality_review", "incomplete_quality_review"}:
        gaps.append(
            {
                "gate": "Generated sample quality review",
                "status": final_report["quality_report"]["status"],
                "detail": final_report["quality_report"]["summary"],
                "next_action": "Create/fill `docs/quality-review.json` only after review readiness reports `review_inputs_ready`.",
            }
        )

    if final_report["cost_report"]["status"] in {"missing_cost_review", "incomplete_cost_review"}:
        gaps.append(
            {
                "gate": "Cloud GPU cost and wait-time review",
                "status": final_report["cost_report"]["status"],
                "detail": final_report["cost_report"]["summary"],
                "next_action": "Fill `docs/cost-review.json` with GPU hourly price, overhead multiplier, max cost, and max wall time.",
            }
        )

    if review_readiness["status"] != "review_inputs_ready":
        gaps.append(
            {
                "gate": "Review input readiness",
                "status": review_readiness["status"],
                "detail": review_readiness["summary"],
                "next_action": "Do not fill quality/cost reviews until required-suite acceptance is ready.",
            }
        )

    if execution_packet["status"] != "ready_for_gpu_handoff":
        gaps.append(
            {
                "gate": "GPU execution handoff",
                "status": execution_packet["status"],
                "detail": execution_packet["summary"],
                "next_action": "Fix failed handoff checks before using cloud GPU time.",
            }
        )

    return gaps


def reproduction_gap_status(final_report, required_suite_acceptance, review_readiness, execution_packet):
    if final_report["status"] in FINAL_READY_STATUSES:
        return "final_decision_ready"
    if execution_packet["status"] != "ready_for_gpu_handoff":
        return "handoff_not_ready"
    if required_suite_acceptance["status"] == "not_ready":
        return "awaiting_gpu_runtime"
    if review_readiness["status"] != "review_inputs_ready":
        return "awaiting_review_inputs"
    if final_report["quality_report"]["status"] in {"missing_quality_review", "incomplete_quality_review"}:
        return "awaiting_quality_review"
    if final_report["cost_report"]["status"] in {"missing_cost_review", "incomplete_cost_review"}:
        return "awaiting_cost_review"
    return "awaiting_final_report_update"


def build_reproduction_gap_report(
    project_root=".",
    log_dir="logs",
    result_dir="outputs/experiment-results",
    p01_result_path="outputs/smoke-test/P01.mp4",
    p01_manifest_path="docs/p01-smoke-manifest.json",
    quality_review_path=None,
    cost_review_path=None,
    repo_url=None,
):
    final_report = build_final_report(
        log_dir=log_dir,
        quality_review_path=quality_review_path,
        cost_review_path=cost_review_path,
    )
    required_suite = build_required_suite_acceptance(
        log_dir=log_dir,
        result_dir=result_dir,
        p01_result_path=p01_result_path,
        p01_manifest_path=p01_manifest_path,
    )
    review_readiness = build_review_readiness(
        log_dir=log_dir,
        result_dir=result_dir,
        p01_result_path=p01_result_path,
        p01_manifest_path=p01_manifest_path,
        quality_review_path=quality_review_path or "docs/quality-review.json",
        cost_review_path=cost_review_path or "docs/cost-review.json",
    )
    execution_packet = build_execution_packet(project_root=project_root, repo_url=repo_url)
    gaps = build_gap_items(final_report, required_suite, review_readiness, execution_packet)
    status = reproduction_gap_status(final_report, required_suite, review_readiness, execution_packet)

    return {
        "status": status,
        "recommendation": final_report["recommendation"],
        "final_report_status": final_report["status"],
        "required_suite_acceptance_status": required_suite["status"],
        "review_readiness_status": review_readiness["status"],
        "gpu_execution_packet_status": execution_packet["status"],
        "gate_statuses": gate_statuses(final_report),
        "missing_required_runtime_cases": missing_runtime_cases(final_report),
        "missing_mobile_video_cases": missing_mobile_cases(final_report),
        "gaps": gaps,
        "next_actions": [item["next_action"] for item in gaps],
        "decision_rule": "The final mobile App recommendation remains provisional until all required runtime, quality, cost, and mobile playback gaps are closed.",
    }


def markdown_gap_report(report):
    lines = [
        "# Reproduction Gap Report",
        "",
        "- Status: `{}`".format(report["status"]),
        "- Recommendation: `{}`".format(report["recommendation"]),
        "- Final report status: `{}`".format(report["final_report_status"]),
        "- Required-suite acceptance: `{}`".format(report["required_suite_acceptance_status"]),
        "- Review readiness: `{}`".format(report["review_readiness_status"]),
        "- GPU execution packet: `{}`".format(report["gpu_execution_packet_status"]),
        "",
        "## Evidence Gates",
        "",
        "| Gate | Status |",
        "| --- | --- |",
    ]
    for gate, status in report["gate_statuses"].items():
        lines.append("| {} | `{}` |".format(gate, status))

    lines.extend(["", "## Open Gaps", "", "| Gate | Status | Detail | Next action |", "| --- | --- | --- | --- |"])
    if report["gaps"]:
        for item in report["gaps"]:
            lines.append(
                "| {gate} | `{status}` | {detail} | {next_action} |".format(**item)
            )
    else:
        lines.append("| - | `none` | No open reproduction gaps. | Update final project decision. |")

    lines.extend(["", "## Decision Rule", "", report["decision_rule"]])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Summarize remaining gaps before final MagiHuman mobile feasibility decision")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--result-dir", default="outputs/experiment-results")
    parser.add_argument("--p01-result-path", default="outputs/smoke-test/P01.mp4")
    parser.add_argument("--p01-manifest", default="docs/p01-smoke-manifest.json")
    parser.add_argument("--quality-review")
    parser.add_argument("--cost-review")
    parser.add_argument("--repo-url")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero unless final decision evidence is ready.")
    args = parser.parse_args()

    report = build_reproduction_gap_report(
        project_root=args.project_root,
        log_dir=args.log_dir,
        result_dir=args.result_dir,
        p01_result_path=args.p01_result_path,
        p01_manifest_path=args.p01_manifest,
        quality_review_path=args.quality_review,
        cost_review_path=args.cost_review,
        repo_url=args.repo_url,
    )
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else markdown_gap_report(report)
    if args.output:
        write_text(args.output, text)
    print(text)
    if args.strict and report["status"] != "final_decision_ready":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
