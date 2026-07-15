import argparse
import json
import shutil
import tarfile
from pathlib import Path, PurePosixPath

from backend.evidence_import import build_import_audit, markdown_import_audit
from backend.evidence_package import build_manifest
from backend.final_report import build_final_report, markdown_final_report


ALLOWED_IMPORT_PREFIXES = ("logs/", "docs/", "outputs/reports/")


def is_safe_member_name(name):
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts


def unique_extract_dir(extract_root, archive_path):
    extract_root = Path(extract_root)
    stem = Path(archive_path).name
    for suffix in (".tar.gz", ".tgz", ".tar"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    candidate = extract_root / stem
    index = 1
    while candidate.exists():
        candidate = extract_root / "{}_{}".format(stem, index)
        index += 1
    return candidate


def extract_archive(archive_path, extract_root="outputs/imported-gpu-evidence"):
    archive_path = Path(archive_path)
    target_dir = unique_extract_dir(extract_root, archive_path)
    target_dir.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive_path, "r:*") as tar:
        members = tar.getmembers()
        unsafe = [member.name for member in members if not is_safe_member_name(member.name)]
        if unsafe:
            raise ValueError("unsafe archive member(s): {}".format(", ".join(unsafe)))
        tar.extractall(target_dir)
    return target_dir


def find_package_dir(extracted_dir):
    extracted_dir = Path(extracted_dir)
    if (extracted_dir / "evidence-manifest.json").is_file():
        return extracted_dir
    candidates = [path for path in extracted_dir.iterdir() if path.is_dir() and (path / "evidence-manifest.json").is_file()]
    if len(candidates) != 1:
        raise ValueError("expected exactly one evidence package directory, found {}".format(len(candidates)))
    return candidates[0]


def importable_files(package_dir):
    package_dir = Path(package_dir)
    files = []
    for path in sorted(package_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(package_dir).as_posix()
        if relative.startswith(ALLOWED_IMPORT_PREFIXES):
            files.append((path, relative))
    return files


def copy_importable_files(package_dir, project_root):
    project_root = Path(project_root)
    imported = []
    for source, relative in importable_files(package_dir):
        target = project_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        imported.append(relative)
    return imported


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")


def build_import_workflow_report(
    archive_path,
    project_root=".",
    extract_root="outputs/imported-gpu-evidence",
    quality_review_path="docs/quality-review.json",
    cost_review_path="docs/cost-review.json",
    final_report_output="docs/mobile-feasibility-report.md",
    import_audit_output="docs/gpu-evidence-import-audit.md",
):
    project_root = Path(project_root)
    extracted_dir = extract_archive(archive_path, extract_root=project_root / extract_root)
    package_dir = find_package_dir(extracted_dir)
    manifest = build_manifest(package_dir)
    if manifest["status"] != "ok":
        return {
            "status": "package_not_imported",
            "archive_path": str(archive_path),
            "extracted_dir": str(extracted_dir),
            "package_dir": str(package_dir),
            "manifest": manifest,
            "imported_files": [],
            "import_audit": None,
            "final_report_status": None,
        }

    imported_files = copy_importable_files(package_dir, project_root)
    quality_path = project_root / quality_review_path
    cost_path = project_root / cost_review_path
    quality_arg = quality_path if quality_path.is_file() else None
    cost_arg = cost_path if cost_path.is_file() else None

    import_audit = build_import_audit(
        log_dir=project_root / "logs",
        quality_review_path=quality_arg,
        cost_review_path=cost_arg,
        final_report_output=project_root / final_report_output,
    )
    final_report = build_final_report(
        log_dir=project_root / "logs",
        quality_review_path=quality_arg,
        cost_review_path=cost_arg,
    )
    write_text(project_root / import_audit_output, markdown_import_audit(import_audit))
    write_text(project_root / final_report_output, markdown_final_report(final_report))

    status = "imported_ready_for_final_update" if import_audit["status"] == "ready_for_final_update" else "imported_incomplete"
    return {
        "status": status,
        "archive_path": str(archive_path),
        "extracted_dir": str(extracted_dir),
        "package_dir": str(package_dir),
        "manifest": manifest,
        "imported_files": imported_files,
        "import_audit": import_audit,
        "final_report_status": final_report["status"],
    }


def markdown_import_workflow_report(report):
    lines = [
        "# GPU Evidence Import Workflow",
        "",
        "- Status: `{}`".format(report["status"]),
        "- Archive: `{}`".format(report["archive_path"]),
        "- Extracted dir: `{}`".format(report["extracted_dir"]),
        "- Package dir: `{}`".format(report["package_dir"]),
        "- Package manifest status: `{}`".format(report["manifest"]["status"]),
        "- Imported file count: {}".format(len(report["imported_files"])),
        "- Final report status: `{}`".format(report["final_report_status"] or "-"),
        "",
        "## Imported Files",
        "",
    ]
    if report["imported_files"]:
        lines.extend("- `{}`".format(path) for path in report["imported_files"])
    else:
        lines.append("- No files imported.")
    if report["manifest"]["forbidden_files"]:
        lines.extend(["", "## Forbidden Files", ""])
        lines.extend("- `{}`".format(item["path"]) for item in report["manifest"]["forbidden_files"])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Import a packaged GPU evidence archive into the local project")
    parser.add_argument("--archive", required=True)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--extract-root", default="outputs/imported-gpu-evidence")
    parser.add_argument("--quality-review", default="docs/quality-review.json")
    parser.add_argument("--cost-review", default="docs/cost-review.json")
    parser.add_argument("--final-report-output", default="docs/mobile-feasibility-report.md")
    parser.add_argument("--import-audit-output", default="docs/gpu-evidence-import-audit.md")
    parser.add_argument("--workflow-output", default="docs/gpu-evidence-import-workflow.md")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if the package is invalid or the import remains incomplete.")
    args = parser.parse_args()

    report = build_import_workflow_report(
        args.archive,
        project_root=args.project_root,
        extract_root=args.extract_root,
        quality_review_path=args.quality_review,
        cost_review_path=args.cost_review,
        final_report_output=args.final_report_output,
        import_audit_output=args.import_audit_output,
    )
    body = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else markdown_import_workflow_report(report)
    output = args.output or args.workflow_output
    if output:
        write_text(Path(args.project_root) / output, body)
    print(body)
    if args.strict and report["status"] != "imported_ready_for_final_update":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
