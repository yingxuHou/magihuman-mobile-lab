import argparse
import json
from pathlib import Path

from backend.evidence_provenance import file_record, run_git
from backend.gpu_bootstrap import DEFAULT_DOCKER_IMAGE, build_bootstrap_plan
from backend.gpu_session_budget import build_session_budget_report
from backend.workflow_readiness_audit import build_workflow_readiness_audit


DEFAULT_REPO_URL = "https://github.com/yingxuHou/magihuman-mobile-lab.git"


def normalize_path(path):
    return str(path).replace("\\", "/")


def check(label, ok, detail):
    return {
        "label": label,
        "ok": bool(ok),
        "detail": detail,
    }


def build_fresh_host_commands(repo_url, branch="main"):
    return [
        "git clone {}".format(repo_url),
        "cd magihuman-mobile-lab",
        "git checkout {}".format(branch),
        "export HF_TOKEN=<your_huggingface_token>",
        "bash scripts/bootstrap_gpu_host.sh",
        "bash outputs/run_magi_container.sh",
    ]


def build_return_commands():
    return [
        "ls -lh outputs/gpu-evidence-*.tar.gz",
        "cp outputs/gpu-evidence-*.tar.gz <local-machine-or-shared-storage>/",
    ]


def build_local_import_commands():
    return [
        ".\\scripts\\import_gpu_evidence_package.ps1 -Archive outputs\\gpu-evidence-<timestamp>.tar.gz",
        "python -m backend.review_readiness --create-templates --format markdown --output docs\\review-readiness.md",
        "python -m backend.final_report --log-dir logs --quality-review docs\\quality-review.json --cost-review docs\\cost-review.json --format markdown --output docs\\mobile-feasibility-report.md",
    ]


def build_local_budget_commands():
    return [
        "python -m backend.gpu_session_budget --create-template --output docs\\gpu-session-budget.json",
        "python -m backend.gpu_session_budget --config docs\\gpu-session-budget.json --format markdown --output docs\\gpu-session-budget-report.md --strict",
    ]


def expected_artifacts():
    return [
        "outputs/reports/gpu_reproduction_workflow_*.md",
        "outputs/reports/p01_acceptance_*.md",
        "outputs/reports/required_suite_acceptance_*.md",
        "docs/review-readiness.md",
        "outputs/gpu-evidence-*.tar.gz",
        "logs/*_metrics.json",
        "outputs/smoke-test/P01.mp4",
        "outputs/experiment-results/P03.mp4",
        "outputs/experiment-results/P04.mp4",
        "outputs/experiment-results/T01.mp4",
        "outputs/experiment-results/T02.mp4",
    ]


def build_execution_packet(
    project_root=".",
    repo_url=None,
    branch="main",
    docker_image=DEFAULT_DOCKER_IMAGE,
    include_optional=False,
    budget_config_path="docs/gpu-session-budget.json",
):
    root = Path(project_root)
    remote = repo_url or run_git(root, "config", "--get", "remote.origin.url") or DEFAULT_REPO_URL
    p01_manifest = file_record(root / "docs" / "p01-smoke-manifest.json")
    workflow_readiness = build_workflow_readiness_audit(project_root=root)
    budget_report = build_session_budget_report(root / budget_config_path if budget_config_path else None)
    bootstrap_plan = build_bootstrap_plan(
        project_root="$PWD",
        image=docker_image,
        download_models=True,
        execute=True,
        include_optional=include_optional,
    )

    bootstrap_script = root / "scripts" / "bootstrap_gpu_host.sh"
    workflow_script = root / "scripts" / "run_gpu_reproduction_workflow.sh"
    import_ps1 = root / "scripts" / "import_gpu_evidence_package.ps1"
    package_script = root / "scripts" / "package_gpu_evidence.sh"

    checks = [
        check("workflow readiness", workflow_readiness["status"] == "ready", workflow_readiness["status"]),
        check("P01 smoke manifest exists", p01_manifest["exists"], p01_manifest["path"]),
        check("Git remote is known", bool(remote), remote or "missing remote"),
        check("GPU bootstrap script exists", bootstrap_script.is_file(), normalize_path(bootstrap_script)),
        check("GPU workflow script exists", workflow_script.is_file(), normalize_path(workflow_script)),
        check("GPU evidence package script exists", package_script.is_file(), normalize_path(package_script)),
        check("local import PowerShell script exists", import_ps1.is_file(), normalize_path(import_ps1)),
        check("GPU session budget guard", budget_report["status"] == "budget_ready", budget_report["status"]),
    ]
    failures = [item for item in checks if not item["ok"]]
    status = "ready_for_gpu_handoff" if not failures else "attention_required"

    return {
        "status": status,
        "summary": "GPU execution packet is ready for a Linux NVIDIA GPU operator." if status == "ready_for_gpu_handoff" else "GPU execution packet needs attention before handoff.",
        "local_runtime_status": "not_executed_on_this_workstation",
        "project_root": normalize_path(root),
        "repo_url": remote,
        "branch": branch,
        "docker_image": docker_image,
        "include_optional": bool(include_optional),
        "budget_config_path": budget_config_path,
        "gpu_session_budget": budget_report,
        "p01_manifest": p01_manifest,
        "checks": checks,
        "failures": failures,
        "gpu_host_requirements": [
            "Linux host with NVIDIA GPU visible to Docker",
            "Docker with NVIDIA Container Toolkit",
            "Hugging Face token with access to required gated model repositories",
            "At least 500 GiB free disk for required-suite checkpoints, caches, logs, and temporary outputs",
            "A completed GPU session budget guard before renting or starting paid GPU time",
        ],
        "local_budget_commands": build_local_budget_commands(),
        "fresh_host_commands": build_fresh_host_commands(remote, branch=branch),
        "container_commands": bootstrap_plan["container_commands"],
        "return_commands": build_return_commands(),
        "local_import_commands": build_local_import_commands(),
        "expected_artifacts": expected_artifacts(),
        "workflow_readiness": workflow_readiness,
        "decision_rule": "Do not change the final mobile App recommendation until imported runtime evidence, quality review, cost review, and final report gates pass.",
    }


def markdown_execution_packet(packet):
    lines = [
        "# GPU Execution Packet",
        "",
        "- Status: `{}`".format(packet["status"]),
        "- Summary: {}".format(packet["summary"]),
        "- Local runtime status: `{}`".format(packet["local_runtime_status"]),
        "- Repository: {}".format(packet["repo_url"]),
        "- Branch: `{}`".format(packet["branch"]),
        "- Docker image: `{}`".format(packet["docker_image"]),
        "- GPU execution provenance: recorded by `scripts/package_gpu_evidence.sh` on the GPU host",
        "- GPU session budget: `{}`".format(packet["gpu_session_budget"]["status"]),
        "- P01 manifest SHA-256: `{}`".format(packet["p01_manifest"].get("sha256") or "-"),
        "",
        "## Handoff Checks",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for item in packet["checks"]:
        lines.append("| {} | {} | {} |".format(item["label"], "ok" if item["ok"] else "failed", item["detail"]))

    lines.extend(["", "## GPU Host Requirements", ""])
    lines.extend("- {}".format(item) for item in packet["gpu_host_requirements"])

    budget = packet["gpu_session_budget"]
    lines.extend(
        [
            "",
            "## Budget Guard Status",
            "",
            "- Status: `{}`".format(budget["status"]),
            "- Summary: {}".format(budget["summary"]),
            "- Config file: {}".format(budget.get("config_path") or "-"),
        ]
    )

    lines.extend(["", "## Local Budget Guard", "", "```powershell"])
    lines.extend(packet["local_budget_commands"])
    lines.append("```")

    lines.extend(["", "## Fresh GPU Host Commands", "", "```bash"])
    lines.extend(packet["fresh_host_commands"])
    lines.append("```")

    lines.extend(["", "## Container Commands", ""])
    for command in packet["container_commands"]:
        lines.extend(["```bash", command, "```"])

    lines.extend(["", "## Expected Artifacts", ""])
    lines.extend("- `{}`".format(item) for item in packet["expected_artifacts"])

    lines.extend(["", "## Return Evidence", "", "```bash"])
    lines.extend(packet["return_commands"])
    lines.append("```")

    lines.extend(["", "## Local Import", "", "```powershell"])
    lines.extend(packet["local_import_commands"])
    lines.append("```")

    lines.extend(
        [
            "",
            "## Decision Rule",
            "",
            packet["decision_rule"],
        ]
    )
    return "\n".join(lines)


def write_output(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Generate the GPU operator handoff packet for MagiHuman reproduction")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--repo-url")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--docker-image", default=DEFAULT_DOCKER_IMAGE)
    parser.add_argument("--include-optional", action="store_true")
    parser.add_argument("--budget-config", default="docs/gpu-session-budget.json")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero unless the handoff packet is ready.")
    args = parser.parse_args()

    packet = build_execution_packet(
        project_root=args.project_root,
        repo_url=args.repo_url,
        branch=args.branch,
        docker_image=args.docker_image,
        include_optional=args.include_optional,
        budget_config_path=args.budget_config,
    )
    text = json.dumps(packet, ensure_ascii=False, indent=2) if args.format == "json" else markdown_execution_packet(packet)
    if args.output:
        write_output(args.output, text)
    print(text)
    if args.strict and packet["status"] != "ready_for_gpu_handoff":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
