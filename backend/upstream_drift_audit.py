import argparse
import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from backend.gpu_bootstrap import MAGIHUMAN_COMMIT, MAGIHUMAN_REPO, MAGICOMPILER_COMMIT, MAGICOMPILER_REPO


SOURCES = [
    {
        "id": "daVinci-MagiHuman-code",
        "kind": "git",
        "source": MAGIHUMAN_REPO,
        "ref": "refs/heads/main",
        "locked_sha": MAGIHUMAN_COMMIT,
    },
    {
        "id": "MagiCompiler-code",
        "kind": "git",
        "source": MAGICOMPILER_REPO,
        "ref": "refs/heads/main",
        "locked_sha": MAGICOMPILER_COMMIT,
    },
    {
        "id": "daVinci-MagiHuman-model",
        "kind": "hf_model",
        "source": "GAIR/daVinci-MagiHuman",
        "api_url": "https://huggingface.co/api/models/GAIR/daVinci-MagiHuman",
        "locked_sha": "7fe95e50c11bd92bdadf94cd51dbec18427f8e0c",
    },
    {
        "id": "daVinci-MagiHuman-space",
        "kind": "hf_space",
        "source": "SII-GAIR/daVinci-MagiHuman",
        "api_url": "https://huggingface.co/api/spaces/SII-GAIR/daVinci-MagiHuman",
        "locked_sha": "f4ca1ddf0ab78843686894301a8d0d7ec2cf027b",
    },
]


def compare_sha(locked_sha, upstream_sha):
    if not upstream_sha:
        return "unreachable"
    if locked_sha == upstream_sha:
        return "matches_lock"
    return "upstream_moved"


def check_git_source(source, runner=None, timeout=30):
    runner = runner or subprocess.run
    command = ["git", "ls-remote", source["source"], source["ref"]]
    try:
        completed = runner(command, capture_output=True, text=True, timeout=timeout)
    except Exception as error:
        return {
            **source,
            "upstream_sha": None,
            "status": "unreachable",
            "detail": str(error),
        }
    if completed.returncode != 0:
        return {
            **source,
            "upstream_sha": None,
            "status": "unreachable",
            "detail": completed.stderr.strip() or "git ls-remote failed",
        }
    first_line = completed.stdout.strip().splitlines()[0] if completed.stdout.strip() else ""
    upstream_sha = first_line.split()[0] if first_line else None
    return {
        **source,
        "upstream_sha": upstream_sha,
        "status": compare_sha(source["locked_sha"], upstream_sha),
        "detail": "git ls-remote {}".format(source["ref"]),
    }


def check_hf_source(source, opener=None, timeout=30):
    opener = opener or urllib.request.urlopen
    try:
        with opener(source["api_url"], timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
        return {
            **source,
            "upstream_sha": None,
            "last_modified": None,
            "status": "unreachable",
            "detail": str(error),
        }
    upstream_sha = data.get("sha")
    return {
        **source,
        "upstream_sha": upstream_sha,
        "last_modified": data.get("lastModified") or data.get("lastModifiedDate"),
        "status": compare_sha(source["locked_sha"], upstream_sha),
        "detail": source["api_url"],
    }


def check_source(source, runner=None, opener=None, timeout=30):
    if source["kind"] == "git":
        return check_git_source(source, runner=runner, timeout=timeout)
    return check_hf_source(source, opener=opener, timeout=timeout)


def build_upstream_drift_audit(sources=None, runner=None, opener=None, timeout=30):
    rows = [
        check_source(source, runner=runner, opener=opener, timeout=timeout)
        for source in (sources or SOURCES)
    ]
    drift = [row for row in rows if row["status"] == "upstream_moved"]
    unreachable = [row for row in rows if row["status"] == "unreachable"]
    if drift:
        status = "drift_detected"
    elif unreachable:
        status = "incomplete"
    else:
        status = "locked_current"
    return {
        "status": status,
        "rows": rows,
        "drift": drift,
        "unreachable": unreachable,
    }


def markdown_upstream_drift_audit(report):
    lines = [
        "# Upstream Drift Audit",
        "",
        "- Status: `{}`".format(report["status"]),
        "",
        "| Source | Kind | Status | Locked SHA | Upstream SHA | Detail |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["rows"]:
        lines.append(
            "| {id} | {kind} | `{status}` | `{locked}` | `{upstream}` | {detail} |".format(
                id=row["id"],
                kind=row["kind"],
                status=row["status"],
                locked=row["locked_sha"],
                upstream=row["upstream_sha"] or "",
                detail=row.get("last_modified") or row["detail"],
            )
        )
    return "\n".join(lines)


def write_output(text, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Check whether locked upstream sources still match current upstream SHAs")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when upstream moved or a source is unreachable.")
    args = parser.parse_args()

    report = build_upstream_drift_audit(timeout=args.timeout)
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else markdown_upstream_drift_audit(report)
    if args.output:
        write_output(text, args.output)
    print(text)
    if args.strict and report["status"] != "locked_current":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
