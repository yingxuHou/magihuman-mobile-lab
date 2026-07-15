import argparse
import json
from pathlib import Path


FORBIDDEN_SUFFIXES = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".safetensors",
    ".ckpt",
    ".pt",
    ".pth",
    ".onnx",
}


def file_info(path, root):
    path = Path(path)
    root = Path(root)
    relative = path.relative_to(root).as_posix()
    return {
        "path": relative,
        "size_bytes": path.stat().st_size,
        "suffix": path.suffix.lower(),
    }


def build_manifest(package_dir):
    package_dir = Path(package_dir)
    files = [
        file_info(path, package_dir)
        for path in sorted(package_dir.rglob("*"))
        if path.is_file()
    ]
    forbidden = [item for item in files if item["suffix"] in FORBIDDEN_SUFFIXES]
    by_top_level = {}
    for item in files:
        top = item["path"].split("/", 1)[0]
        by_top_level[top] = by_top_level.get(top, 0) + 1
    return {
        "status": "contains_forbidden_files" if forbidden else "ok",
        "package_dir": str(package_dir),
        "file_count": len(files),
        "total_size_bytes": sum(item["size_bytes"] for item in files),
        "by_top_level": by_top_level,
        "forbidden_files": forbidden,
        "files": files,
    }


def markdown_manifest(manifest):
    lines = [
        "# GPU Evidence Package Manifest",
        "",
        "- Status: `{}`".format(manifest["status"]),
        "- Package dir: `{}`".format(manifest["package_dir"]),
        "- File count: {}".format(manifest["file_count"]),
        "- Total size bytes: {}".format(manifest["total_size_bytes"]),
        "",
        "| Path | Size bytes |",
        "| --- | ---: |",
    ]
    for item in manifest["files"]:
        lines.append("| `{}` | {} |".format(item["path"], item["size_bytes"]))
    if manifest["forbidden_files"]:
        lines.extend(["", "## Forbidden Files", ""])
        for item in manifest["forbidden_files"]:
            lines.append("- `{}`".format(item["path"]))
    return "\n".join(lines)


def write_output(text, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Create a manifest for a GPU evidence package")
    parser.add_argument("--package-dir", required=True)
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    manifest = build_manifest(args.package_dir)
    text = json.dumps(manifest, ensure_ascii=False, indent=2) if args.format == "json" else markdown_manifest(manifest)
    if args.output:
        write_output(text, args.output)
    print(text)
    if args.strict and manifest["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
