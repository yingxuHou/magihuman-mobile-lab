import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from backend.experiment_matrix import build_matrix


PIPELINE_SEED_DEFAULT = 42
ENGINE_SEED_DEFAULT = 1234


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def relative_path(path, root):
    path = Path(path)
    root = Path(root)
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def file_record(path, root, text=False):
    path = Path(path)
    record = {
        "path": relative_path(path, root),
        "exists": path.exists(),
    }
    if path.exists():
        record["bytes"] = path.stat().st_size
        record["sha256"] = sha256_file(path)
        if text:
            content = path.read_text(encoding="utf-8")
            record["chars"] = len(content)
            record["preview"] = content[:160].replace("\n", " ")
    return record


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def extract_int_flag(script_text, flag):
    match = re.search(r"{}\s+([0-9]+)".format(re.escape(flag)), script_text)
    return int(match.group(1)) if match else None


def git_commit(repo_dir):
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip()


def find_case(case_id):
    for case in build_matrix():
        if case["id"] == case_id:
            return case
    raise ValueError("unknown case id: {}".format(case_id))


def build_p01_manifest(project_root=".", repo_dir="third_party/daVinci-MagiHuman", result_dir="outputs/smoke-test"):
    project_root = Path(project_root)
    repo_dir = Path(repo_dir)
    if not repo_dir.is_absolute():
        repo_dir = project_root / repo_dir

    case = find_case("P01")
    prompt_file = repo_dir / "example" / "assets" / "prompt.txt"
    image_file = repo_dir / "example" / "assets" / "image.png"
    config_file = repo_dir / case["profile"]["config_template"]
    script_file = repo_dir / "example" / "base" / "run_T2V.sh"

    config = read_json(config_file) if config_file.exists() else {}
    script_text = script_file.read_text(encoding="utf-8") if script_file.exists() else ""
    runner_env = dict(case["runner_env"])
    runner_env["MAGIHUMAN_RESULT_PATH"] = "{}/{}.mp4".format(result_dir.rstrip("/"), case["id"])

    manifest = {
        "manifest_type": "p01_smoke_input_manifest",
        "status": "ready_for_gpu_execution"
        if all(path.exists() for path in [prompt_file, image_file, config_file, script_file])
        else "missing_official_assets",
        "source": {
            "repo_dir": relative_path(repo_dir, project_root),
            "commit": git_commit(repo_dir),
        },
        "actual_p01_inputs": {
            "case_id": case["id"],
            "name": case["name"],
            "mode": case["mode"],
            "resolution": case["resolution"],
            "variant": case["variant"],
            "duration_seconds": case["duration_seconds"],
            "seed": case["seed"],
            "prompt": case["prompt"],
            "prompt_sha256": sha256_text(case["prompt"]),
            "reference_image_required": False,
            "reference_image_path": None,
            "audio_path": None,
            "base_width": case["profile"]["br_width"],
            "base_height": case["profile"]["br_height"],
            "sr_width": case["profile"].get("sr_width"),
            "sr_height": case["profile"].get("sr_height"),
            "config_template": case["profile"]["config_template"],
            "runner_env": runner_env,
            "command": "bash scripts/magihuman_task_runner.sh",
            "expected_result_path": runner_env["MAGIHUMAN_RESULT_PATH"],
        },
        "official_example": {
            "base_config": {
                **file_record(config_file, project_root, text=True),
                "engine_seed_default": ENGINE_SEED_DEFAULT,
                "engine_cp_size": config.get("engine_config", {}).get("cp_size"),
                "num_inference_steps": config.get("evaluation_config", {}).get("num_inference_steps"),
                "use_turbo_vae": config.get("evaluation_config", {}).get("use_turbo_vae"),
            },
            "base_t2v_script": {
                **file_record(script_file, project_root, text=True),
                "seconds": extract_int_flag(script_text, "--seconds"),
                "br_width": extract_int_flag(script_text, "--br_width"),
                "br_height": extract_int_flag(script_text, "--br_height"),
                "passes_seed_argument": "--seed" in script_text,
            },
            "prompt_file": file_record(prompt_file, project_root, text=True),
            "reference_image": {
                **file_record(image_file, project_root),
                "used_by_p01": False,
                "used_by_ti2v_cases": True,
            },
        },
        "runtime_defaults": {
            "pipeline_seed_default": PIPELINE_SEED_DEFAULT,
            "engine_seed_default": ENGINE_SEED_DEFAULT,
            "p01_runner_passes_seed": True,
            "official_script_passes_seed": "--seed" in script_text,
        },
        "gpu_commands": {
            "plan": "PREPARE_SOURCES=0 MIN_DISK_GIB=0 bash scripts/run_p01_smoke_pipeline.sh",
            "execute": "INSTALL_MAGICOMPILER=1 DOWNLOAD_MODELS=1 EXECUTE=1 bash scripts/run_p01_smoke_pipeline.sh",
        },
    }
    return manifest


def markdown_report(manifest):
    actual = manifest["actual_p01_inputs"]
    official_script = manifest["official_example"]["base_t2v_script"]
    prompt_file = manifest["official_example"]["prompt_file"]
    image = manifest["official_example"]["reference_image"]

    lines = [
        "# P01 Smoke Input Manifest",
        "",
        "| Field | Value |",
        "| --- | --- |",
        "| Status | `{}` |".format(manifest["status"]),
        "| Source commit | `{}` |".format(manifest["source"].get("commit") or "unknown"),
        "| Case | `{}` / {} |".format(actual["case_id"], actual["name"]),
        "| Mode | `{}` |".format(actual["mode"]),
        "| Resolution | `{}` / {}x{} |".format(actual["resolution"], actual["base_width"], actual["base_height"]),
        "| Duration | {} seconds |".format(actual["duration_seconds"]),
        "| Seed | {} |".format(actual["seed"]),
        "| Prompt SHA-256 | `{}` |".format(actual["prompt_sha256"]),
        "| Reference image required | {} |".format("yes" if actual["reference_image_required"] else "no"),
        "| Expected result | `{}` |".format(actual["expected_result_path"]),
        "| Official script seconds | {} |".format(official_script.get("seconds")),
        "| Official script base size | {}x{} |".format(official_script.get("br_width"), official_script.get("br_height")),
        "| Official prompt file SHA-256 | `{}` |".format(prompt_file.get("sha256", "-")),
        "| Official TI2V image SHA-256 | `{}` |".format(image.get("sha256", "-")),
        "",
        "P01 is a T2V smoke case, so it does not consume the official `example/assets/image.png` reference image. The image hash is still recorded for later TI2V cases.",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate the P01 smoke input manifest")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--repo-dir", default="third_party/daVinci-MagiHuman")
    parser.add_argument("--result-dir", default="outputs/smoke-test")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output")
    args = parser.parse_args()

    manifest = build_p01_manifest(
        project_root=args.project_root,
        repo_dir=args.repo_dir,
        result_dir=args.result_dir,
    )
    text = markdown_report(manifest) if args.format == "markdown" else json.dumps(manifest, ensure_ascii=False, indent=2)

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
