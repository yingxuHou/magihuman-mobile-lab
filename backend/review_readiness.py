import argparse
import json
from pathlib import Path

from backend.cost_review import build_cost_template
from backend.quality_review import build_review_template
from backend.required_suite_acceptance import build_required_suite_acceptance


READY_PREFIX = "ready_for_quality_and_cost_review"


def write_json(data, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(text, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")


def build_quality_template_from_acceptance(acceptance):
    template = build_review_template(case_ids=acceptance["case_ids"])
    result_paths = {row["case_id"]: row.get("result_path") for row in acceptance["rows"]}
    for item in template["case_reviews"]:
        result_path = result_paths.get(item["case_id"])
        if result_path:
            item["sample_path"] = result_path
    return template


def maybe_create_review_inputs(acceptance, quality_review_path, cost_review_path, overwrite=False):
    created = []
    quality_path = Path(quality_review_path)
    cost_path = Path(cost_review_path)

    if overwrite or not quality_path.exists():
        write_json(build_quality_template_from_acceptance(acceptance), quality_path)
        created.append(str(quality_path))

    if overwrite or not cost_path.exists():
        write_json(build_cost_template(case_ids=acceptance["case_ids"]), cost_path)
        created.append(str(cost_path))

    return created


def build_review_readiness(
    log_dir="logs",
    result_dir="outputs/experiment-results",
    p01_result_path="outputs/smoke-test/P01.mp4",
    p01_manifest_path="docs/p01-smoke-manifest.json",
    quality_review_path="docs/quality-review.json",
    cost_review_path="docs/cost-review.json",
    create_templates=False,
    overwrite=False,
    case_ids=None,
    duration_tolerance_seconds=1.0,
):
    acceptance = build_required_suite_acceptance(
        log_dir=log_dir,
        result_dir=result_dir,
        p01_result_path=p01_result_path,
        p01_manifest_path=p01_manifest_path,
        case_ids=case_ids,
        duration_tolerance_seconds=duration_tolerance_seconds,
    )
    runtime_ready = acceptance["status"].startswith(READY_PREFIX)
    created_files = []

    if runtime_ready and create_templates:
        created_files = maybe_create_review_inputs(
            acceptance,
            quality_review_path=quality_review_path,
            cost_review_path=cost_review_path,
            overwrite=overwrite,
        )

    quality_exists = Path(quality_review_path).is_file()
    cost_exists = Path(cost_review_path).is_file()
    if not runtime_ready:
        status = "runtime_not_ready"
        summary = "Required-suite runtime evidence is not ready; do not create or fill review inputs yet."
    elif quality_exists and cost_exists:
        status = "review_inputs_ready"
        summary = "Quality and cost review inputs are ready to be filled."
    else:
        status = "review_inputs_missing"
        summary = "Required-suite runtime evidence is ready, but review input files are missing."

    checks = [
        {
            "label": "required suite ready for review",
            "ok": runtime_ready,
            "detail": acceptance["status"],
        },
        {
            "label": "quality review input exists",
            "ok": quality_exists,
            "detail": str(quality_review_path),
        },
        {
            "label": "cost review input exists",
            "ok": cost_exists,
            "detail": str(cost_review_path),
        },
    ]

    return {
        "status": status,
        "summary": summary,
        "log_dir": str(log_dir),
        "result_dir": str(result_dir),
        "p01_result_path": str(p01_result_path),
        "p01_manifest_path": str(p01_manifest_path),
        "quality_review_path": str(quality_review_path),
        "cost_review_path": str(cost_review_path),
        "create_templates": bool(create_templates),
        "overwrite": bool(overwrite),
        "created_files": created_files,
        "checks": checks,
        "required_suite_acceptance": acceptance,
    }


def markdown_review_readiness(report):
    lines = [
        "# Review Input Readiness",
        "",
        "- Status: `{}`".format(report["status"]),
        "- Summary: {}".format(report["summary"]),
        "- Required-suite status: `{}`".format(report["required_suite_acceptance"]["status"]),
        "- Quality review file: {}".format(report["quality_review_path"]),
        "- Cost review file: {}".format(report["cost_review_path"]),
        "",
        "| Check | OK | Detail |",
        "| --- | --- | --- |",
    ]
    for item in report["checks"]:
        lines.append("| {} | {} | {} |".format(item["label"], "yes" if item["ok"] else "no", item["detail"]))

    if report["created_files"]:
        lines.extend(
            [
                "",
                "## Created Files",
                "",
            ]
        )
        for path in report["created_files"]:
            lines.append("- `{}`".format(path))

    lines.extend(["", "## Next Step", ""])
    if report["status"] == "runtime_not_ready":
        lines.append(
            "Do not create or fill quality/cost review files yet; fix the failed required-suite acceptance checks and rerun GPU cases."
        )
    elif report["status"] == "review_inputs_missing":
        lines.append("Run with `--create-templates` to create the quality and cost review input files.")
    else:
        lines.append(
            "Fill `docs/quality-review.json` and `docs/cost-review.json`, then rerun the final feasibility report with both review files."
        )

    if report["required_suite_acceptance"]["status"] == "ready_for_quality_and_cost_review_with_transcode_required":
        lines.extend(
            [
                "",
                "Runtime evidence can enter review, but final mobile App planning must include a transcode or delivery strategy.",
            ]
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Prepare quality and cost review inputs after required-suite acceptance passes")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--result-dir", default="outputs/experiment-results")
    parser.add_argument("--p01-result-path", default="outputs/smoke-test/P01.mp4")
    parser.add_argument("--p01-manifest", default="docs/p01-smoke-manifest.json")
    parser.add_argument("--quality-review", default="docs/quality-review.json")
    parser.add_argument("--cost-review", default="docs/cost-review.json")
    parser.add_argument("--cases", nargs="+")
    parser.add_argument("--duration-tolerance-seconds", type=float, default=1.0)
    parser.add_argument("--create-templates", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero unless review input files are ready.")
    args = parser.parse_args()

    report = build_review_readiness(
        log_dir=args.log_dir,
        result_dir=args.result_dir,
        p01_result_path=args.p01_result_path,
        p01_manifest_path=args.p01_manifest,
        quality_review_path=args.quality_review,
        cost_review_path=args.cost_review,
        create_templates=args.create_templates,
        overwrite=args.overwrite,
        case_ids=args.cases,
        duration_tolerance_seconds=args.duration_tolerance_seconds,
    )
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else markdown_review_readiness(report)
    if args.output:
        write_text(text, args.output)
    print(text)
    if args.strict and report["status"] != "review_inputs_ready":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
