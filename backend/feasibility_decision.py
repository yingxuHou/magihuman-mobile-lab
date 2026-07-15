import argparse
import json

from backend.experiment_results import build_report
from backend.quality_review import build_quality_report


STATIC_EVIDENCE = {
    "official_model_stack_gib": 201.27,
    "external_model_stack_gib": 84.36,
    "complete_checkpoint_stack_gib": 285.63,
    "base_smoke_dependency_gib": 114.64,
    "mobile_bundle_practical_limit_gib": 4.0,
    "has_official_mobile_export": False,
    "requires_cuda_gpu_runtime": True,
}

OFFICIAL_ON_DEVICE_REASONS = [
    "Complete official checkpoint stack is about 285.63 GiB before cache, logs, and outputs.",
    "The smallest base smoke-test dependency footprint is about 114.64 GiB.",
    "Official scripts use PyTorch torchrun, CUDA/NCCL, MagiCompiler, and Flash Attention.",
    "Static source search found no official ONNX, Core ML, NCNN, MNN, TFLite, or TorchScript export path.",
]

REQUIRED_QUALITY_EVIDENCE = [
    "generated video can be played on a phone",
    "audio exists and is synchronized well enough for demo use",
    "face and motion quality are acceptable in 256p, 540p, and 1080p cases",
    "Mandarin and English TI2V outputs are understandable",
]


def required_rows(report):
    return [row for row in report["rows"] if row.get("required")]


def runtime_evidence(report):
    rows = required_rows(report)
    missing = [row["id"] for row in rows if row["status"] != "measured"]
    measured = [row["id"] for row in rows if row["status"] == "measured"]
    return {
        "state": report["state"]["state"],
        "summary": report["state"]["summary"],
        "required_case_ids": [row["id"] for row in rows],
        "measured_required_case_ids": measured,
        "missing_required_case_ids": missing,
    }


def official_on_device_decision():
    evidence = STATIC_EVIDENCE
    reasons = list(OFFICIAL_ON_DEVICE_REASONS)
    if evidence["complete_checkpoint_stack_gib"] > evidence["mobile_bundle_practical_limit_gib"]:
        reasons.append(
            "Complete checkpoint stack exceeds the project-local mobile package practicality rule "
            "of {:.1f} GiB.".format(evidence["mobile_bundle_practical_limit_gib"])
        )
    return {
        "option": "A",
        "name": "Official on-device inference",
        "status": "not_viable",
        "reasons": reasons,
    }


def cloud_backend_decision(evidence, quality):
    if evidence["missing_required_case_ids"]:
        return {
            "option": "B",
            "name": "Mobile app plus cloud GPU backend",
            "status": "pending_runtime_evidence",
            "reasons": [
                "Backend API, worker, runner, metrics, retry, and retention prototypes exist locally.",
                "Required GPU runtime metrics are still missing: {}.".format(
                    ", ".join(evidence["missing_required_case_ids"])
                ),
                "Latency, VRAM, output validity, quality, and cost must be measured before final product approval.",
            ],
        }
    if quality["status"] in ("missing_quality_review", "incomplete_quality_review"):
        return {
            "option": "B",
            "name": "Mobile app plus cloud GPU backend",
            "status": "measured_needs_quality_review",
            "reasons": [
                "Required GPU runtime metrics exist for all required experiment cases.",
                "Generated samples still need structured quality review.",
            ],
        }
    if quality["status"] == "quality_review_failed":
        return {
            "option": "B",
            "name": "Mobile app plus cloud GPU backend",
            "status": "quality_review_failed",
            "reasons": [
                "Required GPU runtime metrics exist.",
                "One or more generated samples failed the required quality review.",
            ],
        }
    if quality["status"] == "quality_review_passed":
        return {
            "option": "B",
            "name": "Mobile app plus cloud GPU backend",
            "status": "quality_passed_needs_cost_review",
            "reasons": [
                "Required GPU runtime metrics exist and generated samples passed quality review.",
                "A final product decision still needs GPU cost and queueing review.",
            ],
        }
    return {
        "option": "B",
        "name": "Mobile app plus cloud GPU backend",
        "status": "measured_needs_quality_review",
        "reasons": [
            "Required GPU runtime metrics exist for all required experiment cases.",
            "A final product decision still needs quality review and cost review.",
        ],
    }


def stop_decision(evidence, quality):
    if evidence["missing_required_case_ids"]:
        status = "not_decided"
        reasons = ["Stopping productization would be premature before cloud GPU runtime data is collected."]
    elif quality["status"] == "quality_review_failed":
        status = "candidate_quality_failed"
        reasons = ["Stopping productization may be appropriate if failed quality cases cannot be fixed by reruns or prompts."]
    else:
        status = "pending_quality_and_cost_review"
        reasons = ["Use measured latency, VRAM, output quality, and GPU cost to decide whether to stop."]
    return {
        "option": "C",
        "name": "Stop app productization",
        "status": status,
        "reasons": reasons,
    }


def recommended_option(official, cloud):
    if official["status"] == "not_viable" and cloud["status"] == "pending_runtime_evidence":
        return "B_pending_runtime"
    if official["status"] == "not_viable" and cloud["status"] == "measured_needs_quality_review":
        return "B_candidate_needs_quality_review"
    if official["status"] == "not_viable" and cloud["status"] == "quality_passed_needs_cost_review":
        return "B_candidate_needs_cost_review"
    if official["status"] == "not_viable" and cloud["status"] == "quality_review_failed":
        return "C_candidate_quality_failed"
    return "C_needs_manual_review"


def build_decision(matrix_path=None, log_dir="logs", quality_review_path=None):
    report = build_report(matrix_path=matrix_path, log_dir=log_dir)
    evidence = runtime_evidence(report)
    quality = build_quality_report(quality_review_path)
    official = official_on_device_decision()
    cloud = cloud_backend_decision(evidence, quality)
    stop = stop_decision(evidence, quality)
    return {
        "recommendation": recommended_option(official, cloud),
        "static_evidence": STATIC_EVIDENCE,
        "runtime_evidence": evidence,
        "quality_evidence": quality,
        "decisions": {
            "official_on_device": official,
            "cloud_backend": cloud,
            "stop_productization": stop,
        },
        "required_quality_evidence": REQUIRED_QUALITY_EVIDENCE,
        "next_required_actions": next_required_actions(evidence, quality, cloud),
    }


def next_required_actions(evidence, quality, cloud):
    if cloud["status"] == "pending_runtime_evidence":
        return [
            "Run missing required experiment cases on a Linux NVIDIA GPU host: {}.".format(
                ", ".join(evidence["missing_required_case_ids"])
            ),
            "Collect metrics JSON files with wall time, peak VRAM, video metadata, and audio presence.",
            "Review generated samples on mobile devices for playback, quality, and share/save behavior.",
        ]
    if quality["status"] in ("missing_quality_review", "incomplete_quality_review"):
        return [
            "Create or complete the quality review JSON for P01, P03, P04, T01, and T02.",
            "Review each generated video on a phone for playback, lip sync, face quality, motion, speech, and artifacts.",
            "Rerun feasibility decision with --quality-review after the review is complete.",
        ]
    if quality["status"] == "quality_review_failed":
        return [
            "Inspect failed quality cases and decide whether prompt changes or reruns can fix them.",
            "If quality failures persist, prefer option C over productizing the cloud route.",
        ]
    return [
        "Estimate GPU cost per generated video from measured wall time.",
        "Choose final B or C decision for the GitHub project report.",
    ]


def markdown_decision(decision):
    official = decision["decisions"]["official_on_device"]
    cloud = decision["decisions"]["cloud_backend"]
    stop = decision["decisions"]["stop_productization"]
    runtime = decision["runtime_evidence"]
    quality = decision["quality_evidence"]

    lines = [
        "# Mobile Feasibility Decision",
        "",
        "Recommendation: `{}`".format(decision["recommendation"]),
        "",
        "| Option | Track | Status | Evidence |",
        "| --- | --- | --- | --- |",
        "| {option} | {name} | `{status}` | {evidence} |".format(
            option=official["option"],
            name=official["name"],
            status=official["status"],
            evidence=official["reasons"][0],
        ),
        "| {option} | {name} | `{status}` | {evidence} |".format(
            option=cloud["option"],
            name=cloud["name"],
            status=cloud["status"],
            evidence=cloud["reasons"][0],
        ),
        "| {option} | {name} | `{status}` | {evidence} |".format(
            option=stop["option"],
            name=stop["name"],
            status=stop["status"],
            evidence=stop["reasons"][0],
        ),
        "",
        "## Static Evidence",
        "",
        "- Complete checkpoint stack: {:.2f} GiB".format(
            decision["static_evidence"]["complete_checkpoint_stack_gib"]
        ),
        "- Base smoke-test dependency footprint: {:.2f} GiB".format(
            decision["static_evidence"]["base_smoke_dependency_gib"]
        ),
        "- Official mobile export path found: {}".format(
            "yes" if decision["static_evidence"]["has_official_mobile_export"] else "no"
        ),
        "- Requires CUDA GPU runtime: {}".format(
            "yes" if decision["static_evidence"]["requires_cuda_gpu_runtime"] else "no"
        ),
        "",
        "## Runtime Evidence",
        "",
        "- State: `{}`".format(runtime["state"]),
        "- Required cases: {}".format(", ".join(runtime["required_case_ids"])),
        "- Measured required cases: {}".format(", ".join(runtime["measured_required_case_ids"]) or "none"),
        "- Missing required cases: {}".format(", ".join(runtime["missing_required_case_ids"]) or "none"),
        "",
        "## Quality Evidence",
        "",
        "- State: `{}`".format(quality["status"]),
        "- Summary: {}".format(quality["summary"]),
        "- Review file: {}".format(quality["review_path"] or "-"),
        "",
        "## Next Required Actions",
        "",
    ]
    lines.extend("- {}".format(item) for item in decision["next_required_actions"])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Decide MagiHuman mobile feasibility from static and runtime evidence")
    parser.add_argument("--matrix")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--quality-review")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()

    decision = build_decision(matrix_path=args.matrix, log_dir=args.log_dir, quality_review_path=args.quality_review)
    if args.format == "json":
        print(json.dumps(decision, ensure_ascii=False, indent=2))
    else:
        print(markdown_decision(decision))


if __name__ == "__main__":
    main()
