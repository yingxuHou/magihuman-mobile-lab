import argparse
import json
import os
import shlex
import subprocess
from pathlib import Path

from backend.experiment_matrix import build_matrix
from backend.experiment_results import build_summary, load_matrix


def find_case(matrix, case_id):
    for case in matrix:
        if case["id"] == case_id:
            return case
    raise ValueError("unknown case id: {}".format(case_id))


def measured_ids(matrix, log_dir):
    rows = build_summary(matrix, log_dir=log_dir)
    return {row["id"] for row in rows if row["status"] == "measured"}


def dependency_report(case, matrix, log_dir):
    measured = measured_ids(matrix, log_dir)
    missing = [case_id for case_id in case.get("depends_on", []) if case_id not in measured]
    return {
        "ready": not missing,
        "missing": missing,
    }


def shell_export_lines(env):
    return ["export {}={}".format(key, shlex.quote(str(value))) for key, value in sorted(env.items())]


def case_run_plan(case, result_dir="outputs/experiment-results"):
    env = dict(case["runner_env"])
    result_path = "{}/{}.mp4".format(result_dir.rstrip("/"), case["id"])
    env["MAGIHUMAN_RESULT_PATH"] = result_path
    return {
        "case_id": case["id"],
        "name": case["name"],
        "env": env,
        "command": "bash scripts/magihuman_task_runner.sh",
        "result_path": result_path,
    }


def dry_run_text(plan):
    lines = shell_export_lines(plan["env"])
    lines.append(plan["command"])
    return "\n".join(lines)


def execute_plan(plan, cwd=None, timeout_seconds=None):
    env = os.environ.copy()
    env.update({key: str(value) for key, value in plan["env"].items()})
    command = ["bash", "scripts/magihuman_task_runner.sh"]
    return subprocess.run(command, cwd=cwd, env=env, timeout=timeout_seconds)


def main():
    parser = argparse.ArgumentParser(description="Run one MagiHuman experiment case")
    parser.add_argument("--case", dest="case_id", required=True)
    parser.add_argument("--matrix")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--result-dir", default="outputs/experiment-results")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--force", action="store_true", help="Run even if dependencies are missing.")
    parser.add_argument("--timeout-seconds", type=int)
    parser.add_argument("--format", choices=["shell", "json"], default="shell")
    args = parser.parse_args()

    matrix = load_matrix(args.matrix) if args.matrix else build_matrix()
    case = find_case(matrix, args.case_id)
    dependency = dependency_report(case, matrix, args.log_dir)
    plan = case_run_plan(case, result_dir=args.result_dir)

    payload = {
        "case": case,
        "dependency": dependency,
        "plan": plan,
    }

    if not dependency["ready"] and not args.force:
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print("Missing dependencies for {}: {}".format(args.case_id, ", ".join(dependency["missing"])))
            print("Use --force to run anyway.")
        raise SystemExit(2)

    if args.execute:
        completed = execute_plan(plan, cwd=Path.cwd(), timeout_seconds=args.timeout_seconds)
        raise SystemExit(completed.returncode)

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(dry_run_text(plan))


if __name__ == "__main__":
    main()

