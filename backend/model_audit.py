import argparse
import json
from pathlib import Path


GIB = 1024 ** 3

CHECKPOINT_GROUPS = {
    "base": {"path": "daVinci-MagiHuman/base", "expected_gib": 28.54, "min_gib": 27.0},
    "turbo_vae": {"path": "daVinci-MagiHuman/turbo_vae", "expected_gib": 1.74, "min_gib": 1.5},
    "distill": {"path": "daVinci-MagiHuman/distill", "expected_gib": 56.99, "min_gib": 52.0},
    "sr_540p": {"path": "daVinci-MagiHuman/540p_sr", "expected_gib": 56.99, "min_gib": 52.0},
    "sr_1080p": {"path": "daVinci-MagiHuman/1080p_sr", "expected_gib": 56.99, "min_gib": 52.0},
    "t5gemma": {"path": "t5gemma-9b-9b-ul2", "expected_gib": 37.91, "min_gib": 35.0},
    "stable_audio": {"path": "stable-audio-open-1.0", "expected_gib": 14.60, "min_gib": 13.0},
    "wan_vae": {"path": "Wan2.2-TI2V-5B", "expected_gib": 31.85, "min_gib": 29.0},
}

PROFILE_GROUPS = {
    "p01": ["base", "turbo_vae", "t5gemma", "stable_audio", "wan_vae"],
    "required_suite": ["base", "turbo_vae", "sr_540p", "sr_1080p", "t5gemma", "stable_audio", "wan_vae"],
    "complete": ["base", "turbo_vae", "distill", "sr_540p", "sr_1080p", "t5gemma", "stable_audio", "wan_vae"],
}


def directory_size_bytes(path):
    path = Path(path)
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            total += item.stat().st_size
    return total


def audit_group(model_root, group_id, min_size_scale=1.0):
    spec = CHECKPOINT_GROUPS[group_id]
    path = Path(model_root) / spec["path"]
    exists = path.exists()
    size_bytes = directory_size_bytes(path)
    found_gib = size_bytes / GIB
    min_gib = spec["min_gib"] * min_size_scale
    if not exists:
        status = "missing"
    elif found_gib < min_gib:
        status = "too_small"
    else:
        status = "ok"
    return {
        "group": group_id,
        "path": str(path),
        "expected_gib": spec["expected_gib"],
        "min_gib": round(min_gib, 2),
        "found_gib": round(found_gib, 4),
        "size_bytes": size_bytes,
        "exists": exists,
        "status": status,
    }


def build_model_audit(model_root="models", profile="p01", min_size_scale=1.0):
    if profile not in PROFILE_GROUPS:
        raise ValueError("unknown model audit profile: {}".format(profile))
    rows = [audit_group(model_root, group_id, min_size_scale=min_size_scale) for group_id in PROFILE_GROUPS[profile]]
    failures = [row for row in rows if row["status"] != "ok"]
    expected_gib = sum(row["expected_gib"] for row in rows)
    found_gib = sum(row["found_gib"] for row in rows)
    return {
        "status": "ready" if not failures else "not_ready",
        "profile": profile,
        "model_root": str(model_root),
        "expected_gib": round(expected_gib, 2),
        "found_gib": round(found_gib, 4),
        "groups": PROFILE_GROUPS[profile],
        "rows": rows,
        "failures": failures,
    }


def markdown_model_audit(report):
    lines = [
        "# Model Checkpoint Audit",
        "",
        "- Status: `{}`".format(report["status"]),
        "- Profile: `{}`".format(report["profile"]),
        "- Model root: `{}`".format(report["model_root"]),
        "- Expected footprint: {:.2f} GiB".format(report["expected_gib"]),
        "- Found footprint: {:.4f} GiB".format(report["found_gib"]),
        "",
        "| Group | Status | Found GiB | Minimum GiB | Expected GiB | Path |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in report["rows"]:
        lines.append(
            "| {group} | `{status}` | {found:.4f} | {minimum:.2f} | {expected:.2f} | `{path}` |".format(
                group=row["group"],
                status=row["status"],
                found=row["found_gib"],
                minimum=row["min_gib"],
                expected=row["expected_gib"],
                path=row["path"],
            )
        )
    return "\n".join(lines)


def write_output(text, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Audit downloaded MagiHuman checkpoint directories")
    parser.add_argument("--model-root", default="models")
    parser.add_argument("--profile", choices=sorted(PROFILE_GROUPS), default="p01")
    parser.add_argument("--min-size-scale", type=float, default=1.0)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when required model groups are missing or too small.")
    args = parser.parse_args()

    report = build_model_audit(args.model_root, profile=args.profile, min_size_scale=args.min_size_scale)
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else markdown_model_audit(report)
    if args.output:
        write_output(text, args.output)
    print(text)
    if args.strict and report["status"] != "ready":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
