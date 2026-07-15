import argparse
import json
from pathlib import Path

from backend.experiment_results import build_report
from backend.experiment_suite import REQUIRED_CASE_IDS


def build_cost_template(case_ids=None):
    return {
        "review_version": "1",
        "currency": "USD",
        "gpu_name": "",
        "gpu_hourly_usd": None,
        "billing_overhead_multiplier": 1.0,
        "max_cost_per_video_usd": None,
        "max_wall_time_seconds": None,
        "case_ids": list(case_ids or REQUIRED_CASE_IDS),
        "notes": "",
    }


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def number_or_none(value):
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def validate_config(config):
    missing = []
    invalid = []
    for key in ["gpu_hourly_usd", "max_cost_per_video_usd", "max_wall_time_seconds"]:
        value = number_or_none(config.get(key))
        if value is None:
            missing.append(key)
        elif value < 0:
            invalid.append(key)

    overhead = number_or_none(config.get("billing_overhead_multiplier", 1.0))
    if overhead is None:
        missing.append("billing_overhead_multiplier")
    elif overhead <= 0:
        invalid.append("billing_overhead_multiplier")

    return missing, invalid


def rows_by_id(report):
    return {row["id"]: row for row in report["rows"]}


def cost_for_wall_time(wall_time_seconds, gpu_hourly_usd, overhead_multiplier):
    return (wall_time_seconds / 3600.0) * gpu_hourly_usd * overhead_multiplier


def build_cost_rows(config, experiment_report, case_ids):
    gpu_hourly = float(config["gpu_hourly_usd"])
    overhead = float(config.get("billing_overhead_multiplier", 1.0))
    max_cost = float(config["max_cost_per_video_usd"])
    max_wall = float(config["max_wall_time_seconds"])
    rows = []
    source_rows = rows_by_id(experiment_report)

    for case_id in case_ids:
        row = source_rows.get(case_id)
        if not row or row.get("status") != "measured" or row.get("wall_time_seconds") is None:
            rows.append(
                {
                    "case_id": case_id,
                    "status": "missing_runtime_metrics",
                    "wall_time_seconds": None,
                    "cost_per_video_usd": None,
                    "cost_status": "missing",
                    "latency_status": "missing",
                }
            )
            continue

        wall_time = float(row["wall_time_seconds"])
        cost = cost_for_wall_time(wall_time, gpu_hourly, overhead)
        cost_status = "passed" if cost <= max_cost else "failed"
        latency_status = "passed" if wall_time <= max_wall else "failed"
        status = "passed" if cost_status == "passed" and latency_status == "passed" else "failed"
        rows.append(
            {
                "case_id": case_id,
                "status": status,
                "wall_time_seconds": wall_time,
                "cost_per_video_usd": round(cost, 4),
                "cost_status": cost_status,
                "latency_status": latency_status,
                "max_cost_per_video_usd": max_cost,
                "max_wall_time_seconds": max_wall,
            }
        )
    return rows


def build_cost_report(cost_review_path=None, matrix_path=None, log_dir="logs", case_ids=None):
    case_ids = list(case_ids or REQUIRED_CASE_IDS)
    if not cost_review_path:
        return {
            "status": "missing_cost_review",
            "review_path": None,
            "case_ids": case_ids,
            "rows": [],
            "summary": "No cost review file was provided.",
        }

    path = Path(cost_review_path)
    if not path.exists():
        return {
            "status": "missing_cost_review",
            "review_path": str(path),
            "case_ids": case_ids,
            "rows": [],
            "summary": "Cost review file is missing: {}".format(path),
        }

    config = load_json(path)
    case_ids = list(config.get("case_ids") or case_ids)
    missing, invalid = validate_config(config)
    if missing or invalid:
        return {
            "status": "incomplete_cost_review",
            "review_path": str(path),
            "case_ids": case_ids,
            "rows": [],
            "summary": "Cost review config is incomplete.",
            "missing_fields": missing,
            "invalid_fields": invalid,
        }

    experiment_report = build_report(matrix_path=matrix_path, log_dir=log_dir)
    rows = build_cost_rows(config, experiment_report, case_ids)
    row_statuses = {row["status"] for row in rows}

    if "missing_runtime_metrics" in row_statuses:
        status = "incomplete_cost_review"
        summary = "Runtime metrics are missing for one or more cost review cases."
    elif "failed" in row_statuses:
        status = "cost_review_failed"
        summary = "One or more required cases exceeded the cost or latency thresholds."
    else:
        status = "cost_review_passed"
        summary = "All required cases are within the configured cost and latency thresholds."

    return {
        "status": status,
        "review_path": str(path),
        "case_ids": case_ids,
        "currency": config.get("currency", "USD"),
        "gpu_name": config.get("gpu_name", ""),
        "gpu_hourly_usd": float(config["gpu_hourly_usd"]),
        "billing_overhead_multiplier": float(config.get("billing_overhead_multiplier", 1.0)),
        "rows": rows,
        "summary": summary,
    }


def markdown_cost_report(report):
    lines = [
        "# Cost Review",
        "",
        "- Status: `{}`".format(report["status"]),
        "- Summary: {}".format(report["summary"]),
        "- Review file: {}".format(report["review_path"] or "-"),
    ]
    if report.get("gpu_hourly_usd") is not None:
        lines.extend(
            [
                "- GPU: {}".format(report.get("gpu_name") or "-"),
                "- GPU hourly cost: {:.4f} {}".format(report["gpu_hourly_usd"], report.get("currency", "USD")),
                "- Billing overhead multiplier: {:.2f}".format(report["billing_overhead_multiplier"]),
            ]
        )
    if report.get("missing_fields") or report.get("invalid_fields"):
        lines.extend(
            [
                "- Missing fields: {}".format(", ".join(report.get("missing_fields", [])) or "-"),
                "- Invalid fields: {}".format(", ".join(report.get("invalid_fields", [])) or "-"),
            ]
        )
    lines.extend(
        [
            "",
            "| Case | Status | Wall time (s) | Cost/video | Cost status | Latency status |",
            "| --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    if not report["rows"]:
        lines.append("| - | `{}` | - | - | - | - |".format(report["status"]))
        return "\n".join(lines)

    for row in report["rows"]:
        cost = "-" if row.get("cost_per_video_usd") is None else "{:.4f}".format(row["cost_per_video_usd"])
        wall = "-" if row.get("wall_time_seconds") is None else "{:.2f}".format(row["wall_time_seconds"])
        lines.append(
            "| {case} | `{status}` | {wall} | {cost} | {cost_status} | {latency_status} |".format(
                case=row["case_id"],
                status=row["status"],
                wall=wall,
                cost=cost,
                cost_status=row["cost_status"],
                latency_status=row["latency_status"],
            )
        )
    return "\n".join(lines)


def write_json(data, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Create or summarize MagiHuman cloud GPU cost reviews")
    parser.add_argument("--review")
    parser.add_argument("--matrix")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--create-template", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()

    if args.create_template:
        body = build_cost_template()
        text = json.dumps(body, ensure_ascii=False, indent=2)
        if args.output:
            write_json(body, args.output)
        print(text)
        return

    report = build_cost_report(args.review, matrix_path=args.matrix, log_dir=args.log_dir)
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else markdown_cost_report(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
