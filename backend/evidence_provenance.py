import argparse
import hashlib
import json
import subprocess
from pathlib import Path


EXPECTED_DAVINCI_COMMIT = "209209b7086eba2020c5439265221495a8357322"
EXPECTED_MAGICOMPILER_COMMIT = "bfef5bc70226a0c0740e4c551e4f7245a974fb4f"


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_git(repo_dir, *args):
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_dir), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip()


def git_info(repo_dir):
    repo_dir = Path(repo_dir)
    status_text = run_git(repo_dir, "status", "--short") or ""
    dirty_paths = [line for line in status_text.splitlines() if line.strip()]
    return {
        "path": str(repo_dir),
        "exists": repo_dir.exists(),
        "commit": run_git(repo_dir, "rev-parse", "HEAD"),
        "branch": run_git(repo_dir, "branch", "--show-current"),
        "dirty": bool(dirty_paths),
        "dirty_paths": dirty_paths,
    }


def file_record(path):
    path = Path(path)
    record = {
        "path": str(path).replace("\\", "/"),
        "exists": path.exists(),
    }
    if path.exists():
        record["size_bytes"] = path.stat().st_size
        record["sha256"] = sha256_file(path)
    return record


def source_record(project_root, relative_path, expected_commit):
    path = Path(project_root) / relative_path
    info = git_info(path)
    info["expected_commit"] = expected_commit
    info["matches_expected"] = info.get("commit") == expected_commit
    return info


def build_provenance(project_root=".", p01_manifest_path="docs/p01-smoke-manifest.json"):
    project_root = Path(project_root)
    p01_manifest = Path(p01_manifest_path)
    if not p01_manifest.is_absolute():
        p01_manifest = project_root / p01_manifest

    project = git_info(project_root)
    davinci = source_record(project_root, "third_party/daVinci-MagiHuman", EXPECTED_DAVINCI_COMMIT)
    magicompiler = source_record(project_root, "third_party/MagiCompiler", EXPECTED_MAGICOMPILER_COMMIT)
    p01_manifest_record = file_record(p01_manifest)

    blockers = []
    if not project.get("commit"):
        blockers.append("missing_project_commit")
    if not davinci.get("matches_expected"):
        blockers.append("davinci_commit_mismatch")
    if not magicompiler.get("matches_expected"):
        blockers.append("magicompiler_commit_mismatch")
    if not p01_manifest_record.get("exists"):
        blockers.append("missing_p01_manifest")

    return {
        "status": "ok" if not blockers else "attention_required",
        "blockers": blockers,
        "project": project,
        "official_sources": {
            "daVinci-MagiHuman": davinci,
            "MagiCompiler": magicompiler,
        },
        "artifacts": {
            "p01_smoke_manifest": p01_manifest_record,
        },
    }


def markdown_provenance(provenance):
    lines = [
        "# GPU Evidence Provenance",
        "",
        "- Status: `{}`".format(provenance["status"]),
        "- Blockers: {}".format(", ".join(provenance["blockers"]) if provenance["blockers"] else "-"),
        "",
        "## Project",
        "",
        "| Field | Value |",
        "| --- | --- |",
        "| Commit | `{}` |".format(provenance["project"].get("commit") or "-"),
        "| Branch | `{}` |".format(provenance["project"].get("branch") or "-"),
        "| Dirty | `{}` |".format(provenance["project"].get("dirty")),
        "",
        "## Official Sources",
        "",
        "| Source | Commit | Expected | Match |",
        "| --- | --- | --- | --- |",
    ]
    for name, info in provenance["official_sources"].items():
        lines.append(
            "| {} | `{}` | `{}` | `{}` |".format(
                name,
                info.get("commit") or "-",
                info.get("expected_commit") or "-",
                info.get("matches_expected"),
            )
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "| Artifact | Exists | SHA-256 |",
            "| --- | --- | --- |",
        ]
    )
    for name, info in provenance["artifacts"].items():
        lines.append("| {} | `{}` | `{}` |".format(name, info.get("exists"), info.get("sha256") or "-"))
    return "\n".join(lines)


def write_output(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Record provenance for a GPU evidence package")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--p01-manifest", default="docs/p01-smoke-manifest.json")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    provenance = build_provenance(project_root=args.project_root, p01_manifest_path=args.p01_manifest)
    body = json.dumps(provenance, ensure_ascii=False, indent=2) if args.format == "json" else markdown_provenance(provenance)
    if args.output:
        write_output(args.output, body)
    print(body)
    if args.strict and provenance["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
