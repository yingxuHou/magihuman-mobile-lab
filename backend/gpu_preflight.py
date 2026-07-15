import argparse
import json
import shutil
from pathlib import Path


HOST_COMMANDS = [
    ("nvidia-smi", "nvidia-smi", True),
    ("docker", "docker", True),
    ("git", "git", True),
    ("git-lfs", "git-lfs", True),
    ("python", "python", True),
    ("bash", "bash", True),
]

CONTAINER_COMMANDS = [
    ("nvidia-smi", "nvidia-smi", True),
    ("torchrun", "torchrun", True),
    ("python", "python", True),
    ("bash", "bash", True),
    ("ffmpeg", "ffmpeg", False),
    ("ffprobe", "ffprobe", True),
]

MODEL_DIRS = [
    "daVinci-MagiHuman",
    "t5gemma-9b-9b-ul2",
    "stable-audio-open-1.0",
    "Wan2.2-TI2V-5B",
]


def command_check(label, command, required=True, lookup=None):
    lookup = lookup or shutil.which
    resolved = lookup(command)
    return {
        "type": "command",
        "name": label,
        "target": command,
        "required": required,
        "ok": bool(resolved),
        "detail": resolved or "not found on PATH",
    }


def path_check(label, path, required=True, kind="dir"):
    path = Path(path)
    if kind == "file":
        ok = path.is_file()
    else:
        ok = path.is_dir()
    return {
        "type": "path",
        "name": label,
        "target": str(path),
        "required": required,
        "ok": ok,
        "detail": "exists" if ok else "missing",
    }


def disk_check(label, path, min_free_gib, required=True):
    path = Path(path)
    probe = path if path.exists() else Path.cwd()
    usage = shutil.disk_usage(probe)
    free_gib = usage.free / (1024 ** 3)
    ok = free_gib >= min_free_gib
    return {
        "type": "disk",
        "name": label,
        "target": str(path),
        "required": required,
        "ok": ok,
        "detail": "{:.2f} GiB free, {:.2f} GiB required".format(free_gib, min_free_gib),
        "free_gib": round(free_gib, 2),
        "required_gib": min_free_gib,
    }


def build_preflight(
    project_root=".",
    repo_dir="third_party/daVinci-MagiHuman",
    model_root="models",
    mode="host",
    require_models=False,
    min_disk_gib=500.0,
    command_lookup=None,
):
    project_root = Path(project_root)
    repo_dir = Path(repo_dir)
    model_root = Path(model_root)

    commands = HOST_COMMANDS if mode == "host" else CONTAINER_COMMANDS
    checks = [command_check(label, command, required, command_lookup) for label, command, required in commands]
    checks.append(path_check("project root", project_root, required=True))
    checks.append(path_check("official source repo", repo_dir, required=mode == "container" or require_models))
    checks.append(path_check("model root", model_root, required=require_models))

    for model_dir in MODEL_DIRS:
        checks.append(path_check("model {}".format(model_dir), model_root / model_dir, required=require_models))

    checks.append(disk_check("disk free", project_root, min_disk_gib, required=True))

    required_failures = [check for check in checks if check["required"] and not check["ok"]]
    return {
        "mode": mode,
        "status": "ready" if not required_failures else "not_ready",
        "require_models": require_models,
        "min_disk_gib": min_disk_gib,
        "checks": checks,
        "required_failures": required_failures,
    }


def markdown_preflight(report):
    lines = [
        "# GPU Preflight",
        "",
        "- Mode: `{}`".format(report["mode"]),
        "- Status: `{}`".format(report["status"]),
        "- Require models: {}".format("yes" if report["require_models"] else "no"),
        "- Minimum disk: {:.2f} GiB".format(report["min_disk_gib"]),
        "",
        "| Type | Check | Required | Status | Detail |",
        "| --- | --- | --- | --- | --- |",
    ]
    for check in report["checks"]:
        lines.append(
            "| {type} | {name} | {required} | {status} | {detail} |".format(
                type=check["type"],
                name=check["name"],
                required="yes" if check["required"] else "no",
                status="ok" if check["ok"] else "missing",
                detail=check["detail"],
            )
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Check GPU host readiness for MagiHuman reproduction")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--repo-dir", default="third_party/daVinci-MagiHuman")
    parser.add_argument("--model-root", default="models")
    parser.add_argument("--mode", choices=["host", "container"], default="host")
    parser.add_argument("--require-models", action="store_true")
    parser.add_argument("--min-disk-gib", type=float, default=500.0)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    args = parser.parse_args()

    report = build_preflight(
        project_root=args.project_root,
        repo_dir=args.repo_dir,
        model_root=args.model_root,
        mode=args.mode,
        require_models=args.require_models,
        min_disk_gib=args.min_disk_gib,
    )
    body = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else markdown_preflight(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(body + "\n", encoding="utf-8")
    print(body)


if __name__ == "__main__":
    main()
