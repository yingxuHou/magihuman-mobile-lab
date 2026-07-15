import argparse
import json
from pathlib import Path


MAIN_REPO = "GAIR/daVinci-MagiHuman"
EXTERNAL_REPOS = [
    "google/t5gemma-9b-9b-ul2",
    "stabilityai/stable-audio-open-1.0",
    "Wan-AI/Wan2.2-TI2V-5B",
]

PROFILE_RULES = {
    "p01": {
        "required_groups": ["base", "turbo_vae"],
        "forbidden_groups": ["540p_sr", "1080p_sr", "distill"],
        "requires_include_filters": True,
    },
    "required_suite": {
        "required_groups": ["base", "turbo_vae", "540p_sr", "1080p_sr"],
        "forbidden_groups": ["distill"],
        "requires_include_filters": True,
    },
    "complete": {
        "required_groups": [],
        "forbidden_groups": [],
        "requires_include_filters": False,
    },
}


def command_lines(log_text):
    return [line for line in log_text.splitlines() if line.startswith("download_command=")]


def normalize(text):
    return text.replace("\\*", "*").replace("'", "").replace('"', "")


def contains_group(line, group):
    normalized = normalize(line)
    return "{}/".format(group) in normalized or "{}/*".format(group) in normalized


def row(label, ok, detail):
    return {"label": label, "ok": ok, "detail": detail}


def build_download_log_audit(profile="p01", log_path=None, log_text=None):
    if profile not in PROFILE_RULES:
        raise ValueError("unknown download log audit profile: {}".format(profile))
    if log_text is None:
        log_text = Path(log_path).read_text(encoding="utf-8", errors="replace")
    lines = command_lines(log_text)
    main_lines = [line for line in lines if MAIN_REPO in line]
    external_lines = {repo: [line for line in lines if repo in line] for repo in EXTERNAL_REPOS}
    main_line = main_lines[0] if main_lines else ""
    rules = PROFILE_RULES[profile]

    checks = [
        row("download command lines present", bool(lines), "{} command line(s)".format(len(lines))),
        row("main model command present", bool(main_lines), MAIN_REPO),
    ]

    for group in rules["required_groups"]:
        checks.append(
            row(
                "main group {} included".format(group),
                contains_group(main_line, group),
                "expected --include {}/*".format(group),
            )
        )
    for group in rules["forbidden_groups"]:
        found = any(contains_group(line, group) for line in main_lines)
        checks.append(
            row(
                "main group {} not requested".format(group),
                not found,
                "forbidden for profile {}".format(profile),
            )
        )

    if rules["requires_include_filters"]:
        checks.append(
            row(
                "main command uses include filters",
                "--include" in main_line,
                "profile {} should use explicit --include filters".format(profile),
            )
        )
    else:
        checks.append(
            row(
                "complete command has no include filters",
                bool(main_line) and "--include" not in main_line,
                "complete profile should mirror the full main repository",
            )
        )

    for repo, repo_lines in external_lines.items():
        checks.append(row("external repo {} requested".format(repo), bool(repo_lines), repo))

    failures = [check for check in checks if not check["ok"]]
    return {
        "status": "ready" if not failures else "not_ready",
        "profile": profile,
        "log_path": str(log_path) if log_path else None,
        "command_count": len(lines),
        "checks": checks,
        "failures": failures,
        "download_commands": lines,
    }


def markdown_download_log_audit(report):
    lines = [
        "# Download Log Audit",
        "",
        "- Status: `{}`".format(report["status"]),
        "- Profile: `{}`".format(report["profile"]),
        "- Log path: `{}`".format(report["log_path"] or "-"),
        "- Download commands: {}".format(report["command_count"]),
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for check in report["checks"]:
        lines.append(
            "| {label} | {status} | {detail} |".format(
                label=check["label"],
                status="ok" if check["ok"] else "failed",
                detail=check["detail"],
            )
        )
    return "\n".join(lines)


def write_output(text, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Audit checkpoint download logs for expected Hugging Face repository groups")
    parser.add_argument("--profile", choices=sorted(PROFILE_RULES), default="p01")
    parser.add_argument("--log", required=True)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when download log does not match the selected profile.")
    args = parser.parse_args()

    report = build_download_log_audit(profile=args.profile, log_path=args.log)
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else markdown_download_log_audit(report)
    if args.output:
        write_output(text, args.output)
    print(text)
    if args.strict and report["status"] != "ready":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
