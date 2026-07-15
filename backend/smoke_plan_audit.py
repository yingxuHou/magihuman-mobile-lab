import argparse
import json
from pathlib import Path

from backend.experiment_matrix import build_matrix
from backend.experiment_suite import build_suite_plan
from backend.smoke_manifest import sha256_text


EXPECTED_ENV_FIELDS = [
    "MAGIHUMAN_TASK_ID",
    "MAGIHUMAN_PROMPT",
    "MAGIHUMAN_MODE",
    "MAGIHUMAN_RESOLUTION",
    "MAGIHUMAN_DURATION_SECONDS",
    "MAGIHUMAN_SEED",
    "MAGIHUMAN_MODEL_VARIANT",
    "MAGIHUMAN_RESULT_PATH",
    "MAGIHUMAN_MANIFEST_PATH",
]


def load_manifest(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def find_matrix_case(case_id):
    for case in build_matrix():
        if case["id"] == case_id:
            return case
    raise ValueError("unknown case id: {}".format(case_id))


def comparison(label, manifest_value, plan_value):
    return {
        "label": label,
        "manifest_value": manifest_value,
        "plan_value": plan_value,
        "ok": manifest_value == plan_value,
    }


def build_expected_plan(log_dir="logs", result_dir="outputs/smoke-test"):
    suite = build_suite_plan(case_ids=["P01"], log_dir=log_dir, result_dir=result_dir, rerun=True)
    if len(suite["steps"]) != 1:
        raise ValueError("expected exactly one P01 suite step")
    return suite["steps"][0]["plan"]


def build_smoke_plan_audit(
    manifest_path="docs/p01-smoke-manifest.json",
    manifest=None,
    log_dir="logs",
    result_dir="outputs/smoke-test",
):
    manifest = manifest or load_manifest(manifest_path)
    actual = manifest["actual_p01_inputs"]
    plan = build_expected_plan(log_dir=log_dir, result_dir=result_dir)
    case = find_matrix_case("P01")
    env = plan["env"]

    checks = [
        comparison("manifest_type", manifest.get("manifest_type"), "p01_smoke_input_manifest"),
        comparison("case_id", actual.get("case_id"), "P01"),
        comparison("case_name", actual.get("name"), case["name"]),
        comparison("mode", actual.get("mode"), case["mode"]),
        comparison("resolution", actual.get("resolution"), case["resolution"]),
        comparison("variant", actual.get("variant"), case["variant"]),
        comparison("duration_seconds", actual.get("duration_seconds"), case["duration_seconds"]),
        comparison("seed", actual.get("seed"), case["seed"]),
        comparison("prompt_sha256", actual.get("prompt_sha256"), sha256_text(case["prompt"])),
        comparison("base_width", actual.get("base_width"), case["profile"]["br_width"]),
        comparison("base_height", actual.get("base_height"), case["profile"]["br_height"]),
        comparison("sr_width", actual.get("sr_width"), case["profile"].get("sr_width")),
        comparison("sr_height", actual.get("sr_height"), case["profile"].get("sr_height")),
        comparison("command", actual.get("command"), plan["command"]),
        comparison("expected_result_path", actual.get("expected_result_path"), plan["result_path"]),
    ]
    manifest_env = actual.get("runner_env", {})
    for field in EXPECTED_ENV_FIELDS:
        checks.append(comparison("env.{}".format(field), manifest_env.get(field), env.get(field)))

    failures = [check for check in checks if not check["ok"]]
    return {
        "status": "ready" if not failures else "not_ready",
        "manifest_path": str(manifest_path),
        "log_dir": str(log_dir),
        "result_dir": str(result_dir),
        "plan": plan,
        "checks": checks,
        "failures": failures,
    }


def markdown_smoke_plan_audit(report):
    def render(value):
        return "null" if value is None else value

    lines = [
        "# P01 Smoke Plan Audit",
        "",
        "- Status: `{}`".format(report["status"]),
        "- Manifest path: `{}`".format(report["manifest_path"]),
        "- Result dir: `{}`".format(report["result_dir"]),
        "",
        "| Check | Status | Manifest | Plan |",
        "| --- | --- | --- | --- |",
    ]
    for check in report["checks"]:
        lines.append(
            "| {label} | {status} | `{manifest}` | `{plan}` |".format(
                label=check["label"],
                status="ok" if check["ok"] else "mismatch",
                manifest=render(check["manifest_value"]),
                plan=render(check["plan_value"]),
            )
        )
    return "\n".join(lines)


def write_output(text, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Compare the P01 smoke manifest against the current P01 execution plan")
    parser.add_argument("--manifest", default="docs/p01-smoke-manifest.json")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--result-dir", default="outputs/smoke-test")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when manifest and plan do not match.")
    args = parser.parse_args()

    report = build_smoke_plan_audit(manifest_path=args.manifest, log_dir=args.log_dir, result_dir=args.result_dir)
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else markdown_smoke_plan_audit(report)
    if args.output:
        write_output(text, args.output)
    print(text)
    if args.strict and report["status"] != "ready":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
