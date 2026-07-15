import argparse
import json
from pathlib import Path

from backend.experiment_matrix import build_matrix
from backend.experiment_results import build_summary, load_matrix
from backend.experiment_runner import case_run_plan, dry_run_text, execute_plan, find_case


REQUIRED_CASE_IDS = ["P01", "P03", "P04", "T01", "T02"]
OPTIONAL_CASE_IDS = ["P02", "T03", "T04"]


def default_case_ids(include_optional=False):
    if include_optional:
        return ["P01", "P02", "P03", "P04", "T01", "T02", "T03", "T04"]
    return list(REQUIRED_CASE_IDS)


def rows_by_id(matrix, log_dir):
    return {row["id"]: row for row in build_summary(matrix, log_dir=log_dir)}


def measured_case_ids(rows):
    return {case_id for case_id, row in rows.items() if row["status"] == "measured"}


def build_suite_plan(
    matrix=None,
    case_ids=None,
    log_dir="logs",
    result_dir="outputs/experiment-results",
    include_optional=False,
    rerun=False,
):
    matrix = matrix or build_matrix()
    case_ids = list(case_ids) if case_ids else default_case_ids(include_optional=include_optional)
    rows = rows_by_id(matrix, log_dir)
    ready_or_planned = set(measured_case_ids(rows))
    steps = []

    for case_id in case_ids:
        case = find_case(matrix, case_id)
        row = rows.get(case_id, {"status": "missing_metrics", "metrics_path": None})
        dependencies = list(case.get("depends_on", []))
        missing_dependencies = [dependency for dependency in dependencies if dependency not in ready_or_planned]

        if row["status"] == "measured" and not rerun:
            action = "skip_measured"
            ready = True
            ready_or_planned.add(case_id)
        elif missing_dependencies:
            action = "blocked"
            ready = False
        else:
            action = "run"
            ready = True
            ready_or_planned.add(case_id)

        steps.append(
            {
                "case_id": case_id,
                "name": case["name"],
                "required": case["required"],
                "dependencies": dependencies,
                "missing_dependencies": missing_dependencies,
                "metrics_status": row["status"],
                "metrics_path": row.get("metrics_path"),
                "action": action,
                "ready": ready,
                "plan": case_run_plan(case, result_dir=result_dir),
            }
        )

    status = "ready"
    if any(step["action"] == "blocked" for step in steps):
        status = "blocked"
    elif all(step["action"] == "skip_measured" for step in steps):
        status = "already_measured"

    return {
        "status": status,
        "log_dir": str(log_dir),
        "result_dir": result_dir,
        "case_ids": case_ids,
        "steps": steps,
    }


def suite_shell_text(suite):
    lines = []
    for step in suite["steps"]:
        lines.append("# {case_id} {name}: {action}".format(**step))
        if step["action"] == "blocked":
            lines.append("# missing dependencies: {}".format(", ".join(step["missing_dependencies"])))
            lines.append("")
            continue
        if step["action"] == "skip_measured":
            lines.append("# metrics already exist: {}".format(step["metrics_path"]))
            lines.append("")
            continue
        lines.append(dry_run_text(step["plan"]))
        lines.append("")
    return "\n".join(lines).rstrip()


def markdown_suite(suite):
    lines = [
        "| Case | Action | Metrics | Dependencies | Missing dependencies | Result path |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for step in suite["steps"]:
        lines.append(
            "| {case} | `{action}` | `{metrics}` | {deps} | {missing} | {result} |".format(
                case=step["case_id"],
                action=step["action"],
                metrics=step["metrics_status"],
                deps=", ".join(step["dependencies"]) if step["dependencies"] else "-",
                missing=", ".join(step["missing_dependencies"]) if step["missing_dependencies"] else "-",
                result=step["plan"]["result_path"],
            )
        )
    return "\n".join(lines)


def execute_suite(suite, cwd=None, timeout_seconds=None, force=False):
    results = []
    for step in suite["steps"]:
        if step["action"] == "skip_measured" and not force:
            results.append({"case_id": step["case_id"], "action": "skip_measured", "returncode": 0})
            continue
        if step["action"] == "blocked" and not force:
            results.append({"case_id": step["case_id"], "action": "blocked", "returncode": 2})
            break
        completed = execute_plan(step["plan"], cwd=cwd, timeout_seconds=timeout_seconds)
        results.append({"case_id": step["case_id"], "action": "run", "returncode": completed.returncode})
        if completed.returncode != 0:
            break
    return results


def main():
    parser = argparse.ArgumentParser(description="Plan or run the required MagiHuman GPU experiment suite")
    parser.add_argument("--matrix")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--result-dir", default="outputs/experiment-results")
    parser.add_argument("--cases", nargs="+")
    parser.add_argument("--include-optional", action="store_true")
    parser.add_argument("--rerun", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--force", action="store_true", help="Run even when a selected case is blocked or measured.")
    parser.add_argument("--timeout-seconds", type=int)
    parser.add_argument("--format", choices=["shell", "json", "markdown"], default="shell")
    args = parser.parse_args()

    matrix = load_matrix(args.matrix) if args.matrix else build_matrix()
    suite = build_suite_plan(
        matrix=matrix,
        case_ids=args.cases,
        log_dir=args.log_dir,
        result_dir=args.result_dir,
        include_optional=args.include_optional,
        rerun=args.rerun,
    )

    if args.execute:
        results = execute_suite(suite, cwd=Path.cwd(), timeout_seconds=args.timeout_seconds, force=args.force)
        print(json.dumps({"suite": suite, "results": results}, ensure_ascii=False, indent=2))
        raise SystemExit(max(result["returncode"] for result in results) if results else 0)

    if suite["status"] == "blocked" and not args.force:
        exit_code = 2
    else:
        exit_code = 0

    if args.format == "json":
        print(json.dumps(suite, ensure_ascii=False, indent=2))
    elif args.format == "markdown":
        print(markdown_suite(suite))
    else:
        print(suite_shell_text(suite))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
