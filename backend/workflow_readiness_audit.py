import argparse
import json
from pathlib import Path

from backend.gpu_bootstrap import container_commands


def read_text(root, relative_path):
    path = Path(root) / relative_path
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def row(label, ok, detail):
    return {
        "label": label,
        "ok": bool(ok),
        "detail": detail,
    }


def contains(text, needle):
    return text is not None and needle in text


def ordered(text, needles):
    if text is None:
        return False
    cursor = -1
    for needle in needles:
        index = text.find(needle, cursor + 1)
        if index < 0:
            return False
        cursor = index
    return True


def build_workflow_readiness_audit(project_root="."):
    root = Path(project_root)
    workflow = read_text(root, "scripts/run_gpu_reproduction_workflow.sh")
    p01_pipeline = read_text(root, "scripts/run_p01_smoke_pipeline.sh")
    full_pipeline = read_text(root, "scripts/gpu_reproduction_pipeline.sh")
    package_script = read_text(root, "scripts/package_gpu_evidence.sh")
    bootstrap_execute_commands = container_commands(download_models=True, execute=True)
    bootstrap_execute_text = "\n".join(bootstrap_execute_commands)

    rows = [
        row("workflow script exists", workflow is not None, "scripts/run_gpu_reproduction_workflow.sh"),
        row("workflow runs upstream drift audit strictly", contains(workflow, "backend.upstream_drift_audit") and contains(workflow, "--strict"), "upstream drift audit before GPU work"),
        row("workflow prepares locked sources", contains(workflow, "scripts/prepare_sources.sh"), "locked source preparation is present"),
        row(
            "workflow order is P01 before full suite before package",
            ordered(workflow, ["scripts/run_p01_smoke_pipeline.sh", "scripts/gpu_reproduction_pipeline.sh", "scripts/package_gpu_evidence.sh"]),
            "P01-first execution order",
        ),
        row("workflow forces P01 execution", contains(workflow, "EXECUTE=1 MODEL_PROFILE=p01"), "P01 pipeline executes with p01 profile"),
        row("workflow forces required-suite execution", contains(workflow, "EXECUTE=1 MODEL_PROFILE=required_suite"), "full pipeline executes with required_suite profile"),
        row("workflow disables nested source prep", contains(workflow, "env PREPARE_SOURCES=0"), "pipelines do not repeat source preparation"),
        row("P01 pipeline has strict acceptance gate", contains(p01_pipeline, "backend.p01_acceptance") and contains(p01_pipeline, "--strict"), "P01 acceptance blocks full suite"),
        row(
            "full pipeline has strict required-suite gate",
            contains(full_pipeline, "backend.required_suite_acceptance") and contains(full_pipeline, "--strict"),
            "required-suite acceptance blocks quality/cost review",
        ),
        row("package includes P01 acceptance JSON", contains(package_script, "*p01_acceptance*.json"), "P01 gate evidence enters package"),
        row("package includes required-suite acceptance JSON", contains(package_script, "*required_suite_acceptance*.json"), "full-suite gate evidence enters package"),
        row(
            "bootstrap execute mode uses workflow",
            "bash scripts/run_gpu_reproduction_workflow.sh" in bootstrap_execute_text,
            "gpu_bootstrap execute path",
        ),
    ]
    failures = [item for item in rows if not item["ok"]]
    return {
        "status": "ready" if not failures else "not_ready",
        "project_root": str(project_root),
        "rows": rows,
        "failures": failures,
    }


def markdown_workflow_readiness_audit(audit):
    lines = [
        "# GPU Workflow Readiness Audit",
        "",
        "- Status: `{}`".format(audit["status"]),
        "- Project root: `{}`".format(audit["project_root"]),
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for item in audit["rows"]:
        lines.append(
            "| {label} | {status} | {detail} |".format(
                label=item["label"],
                status="ok" if item["ok"] else "failed",
                detail=item["detail"],
            )
        )
    if audit["status"] == "ready":
        lines.extend(["", "The GPU reproduction workflow is ready to run on a prepared GPU host."])
    else:
        lines.extend(["", "Do not run GPU reproduction until failed workflow checks are fixed."])
    return "\n".join(lines)


def write_output(text, output):
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Audit the GPU workflow command chain before expensive reproduction runs")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when workflow readiness checks fail.")
    args = parser.parse_args()

    audit = build_workflow_readiness_audit(project_root=args.project_root)
    text = json.dumps(audit, ensure_ascii=False, indent=2) if args.format == "json" else markdown_workflow_readiness_audit(audit)
    if args.output:
        write_output(text, args.output)
    print(text)
    if args.strict and audit["status"] != "ready":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
