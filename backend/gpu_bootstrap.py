import argparse
import json
from pathlib import Path


DEFAULT_DOCKER_IMAGE = "sandai/magi-human:latest"
DEFAULT_CONTAINER_NAME = "magihuman-lab"
MAGIHUMAN_REPO = "https://github.com/GAIR-NLP/daVinci-MagiHuman.git"
MAGIHUMAN_COMMIT = "209209b7086eba2020c5439265221495a8357322"
MAGICOMPILER_REPO = "https://github.com/SandAI-org/MagiCompiler.git"
MAGICOMPILER_COMMIT = "bfef5bc70226a0c0740e4c551e4f7245a974fb4f"


def docker_run_command(project_root="$PWD", image=DEFAULT_DOCKER_IMAGE, container_name=DEFAULT_CONTAINER_NAME):
    return " ".join(
        [
            "docker run --rm -it",
            "--gpus all",
            "--network host",
            "--ipc host",
            "--shm-size 64g",
            "--name {}".format(container_name),
            "-e HF_TOKEN",
            "-e HUGGINGFACE_HUB_TOKEN",
            '-v "{}:/repo"'.format(project_root),
            "-w /repo",
            image,
            "bash",
        ]
    )


def container_commands(download_models=False, execute=False, include_optional=False):
    commands = [
        "INSTALL_MAGICOMPILER=1 bash scripts/prepare_sources.sh",
        "python -m backend.gpu_preflight --mode container --format markdown",
    ]
    env_parts = ["PREPARE_SOURCES=0"]
    if download_models:
        env_parts.append("DOWNLOAD_MODELS=1")
    if execute:
        env_parts.append("EXECUTE=1")
    if include_optional:
        env_parts.append("INCLUDE_OPTIONAL=1")
    env_parts.append("bash scripts/gpu_reproduction_pipeline.sh")
    commands.append(" ".join(env_parts))
    commands.append("bash scripts/package_gpu_evidence.sh")
    return commands


def build_bootstrap_plan(
    project_root="$PWD",
    image=DEFAULT_DOCKER_IMAGE,
    container_name=DEFAULT_CONTAINER_NAME,
    download_models=False,
    execute=False,
    include_optional=False,
):
    return {
        "docker_image": image,
        "container_name": container_name,
        "project_root": project_root,
        "verified_sources": {
            "daVinci-MagiHuman": {
                "repo": MAGIHUMAN_REPO,
                "commit": MAGIHUMAN_COMMIT,
                "path": "third_party/daVinci-MagiHuman",
            },
            "MagiCompiler": {
                "repo": MAGICOMPILER_REPO,
                "commit": MAGICOMPILER_COMMIT,
                "path": "third_party/MagiCompiler",
            },
        },
        "host_commands": [
            "python -m backend.gpu_preflight --mode host --format markdown",
            "docker pull {}".format(image),
            docker_run_command(project_root=project_root, image=image, container_name=container_name),
        ],
        "container_commands": container_commands(
            download_models=download_models,
            execute=execute,
            include_optional=include_optional,
        ),
    }


def markdown_plan(plan):
    lines = [
        "# GPU Bootstrap Plan",
        "",
        "- Docker image: `{}`".format(plan["docker_image"]),
        "- Container name: `{}`".format(plan["container_name"]),
        "- Project root mount: `{}`".format(plan["project_root"]),
        "",
        "## Verified Sources",
        "",
        "| Source | Repo | Commit | Local path |",
        "| --- | --- | --- | --- |",
    ]
    for name, source in plan["verified_sources"].items():
        lines.append(
            "| {} | {} | `{}` | `{}` |".format(name, source["repo"], source["commit"], source["path"])
        )
    lines.extend(["", "## Host Commands", ""])
    lines.extend("```bash\n{}\n```".format(command) for command in plan["host_commands"])
    lines.extend(["", "## Container Commands", ""])
    lines.extend("```bash\n{}\n```".format(command) for command in plan["container_commands"])
    return "\n".join(lines)


def shell_plan(plan):
    lines = ["#!/usr/bin/env bash", "set -euo pipefail", ""]
    lines.extend(plan["host_commands"])
    return "\n".join(lines)


def write_output(text, output):
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Generate GPU bootstrap commands for MagiHuman reproduction")
    parser.add_argument("--project-root", default="$PWD")
    parser.add_argument("--image", default=DEFAULT_DOCKER_IMAGE)
    parser.add_argument("--container-name", default=DEFAULT_CONTAINER_NAME)
    parser.add_argument("--download-models", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--include-optional", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["json", "markdown", "shell"], default="markdown")
    args = parser.parse_args()

    plan = build_bootstrap_plan(
        project_root=args.project_root,
        image=args.image,
        container_name=args.container_name,
        download_models=args.download_models,
        execute=args.execute,
        include_optional=args.include_optional,
    )
    if args.format == "json":
        text = json.dumps(plan, ensure_ascii=False, indent=2)
    elif args.format == "shell":
        text = shell_plan(plan)
    else:
        text = markdown_plan(plan)
    if args.output:
        write_output(text, args.output)
    print(text)


if __name__ == "__main__":
    main()
