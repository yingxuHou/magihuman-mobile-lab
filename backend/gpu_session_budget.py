import argparse
import json
from pathlib import Path

from backend.model_audit import CHECKPOINT_GROUPS, PROFILE_GROUPS


DEFAULT_OUTPUT_BUFFER_GIB = 100.0


def build_budget_template(profile="p01"):
    return {
        "budget_version": "1",
        "currency": "USD",
        "gpu_provider": "",
        "gpu_name": "",
        "checkpoint_profile": profile,
        "gpu_hourly_usd": None,
        "billing_overhead_multiplier": 1.25,
        "max_session_hours": None,
        "max_session_budget_usd": None,
        "disk_budget_gib": None,
        "output_buffer_gib": DEFAULT_OUTPUT_BUFFER_GIB,
        "stop_policy": "stop_before_download_if_over_budget",
        "notes": "Fill this before renting GPU time. Do not use provider prices from memory; verify the current price first.",
    }


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def number_or_none(value):
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def expected_checkpoint_gib(profile):
    if profile not in PROFILE_GROUPS:
        raise ValueError("unknown checkpoint profile: {}".format(profile))
    return round(sum(CHECKPOINT_GROUPS[group]["expected_gib"] for group in PROFILE_GROUPS[profile]), 2)


def validate_config(config):
    missing = []
    invalid = []

    profile = config.get("checkpoint_profile", "p01")
    if profile not in PROFILE_GROUPS:
        invalid.append("checkpoint_profile")

    for key in ["gpu_hourly_usd", "max_session_hours", "max_session_budget_usd", "disk_budget_gib"]:
        value = number_or_none(config.get(key))
        if value is None:
            missing.append(key)
        elif value <= 0:
            invalid.append(key)

    overhead = number_or_none(config.get("billing_overhead_multiplier", 1.0))
    if overhead is None:
        missing.append("billing_overhead_multiplier")
    elif overhead <= 0:
        invalid.append("billing_overhead_multiplier")

    output_buffer = number_or_none(config.get("output_buffer_gib", DEFAULT_OUTPUT_BUFFER_GIB))
    if output_buffer is None:
        missing.append("output_buffer_gib")
    elif output_buffer < 0:
        invalid.append("output_buffer_gib")

    return missing, invalid


def build_budget_rows(report):
    rows = []
    rows.append(
        {
            "check": "budget config complete",
            "status": "passed" if not report.get("missing_fields") and not report.get("invalid_fields") else "failed",
            "detail": "missing: {}; invalid: {}".format(
                ", ".join(report.get("missing_fields", [])) or "-",
                ", ".join(report.get("invalid_fields", [])) or "-",
            ),
        }
    )
    if report.get("estimated_session_cost_usd") is not None:
        rows.append(
            {
                "check": "estimated session cost within cap",
                "status": "passed" if report["estimated_session_cost_usd"] <= report["max_session_budget_usd"] else "failed",
                "detail": "{:.4f} <= {:.4f} {}".format(
                    report["estimated_session_cost_usd"],
                    report["max_session_budget_usd"],
                    report["currency"],
                ),
            }
        )
        rows.append(
            {
                "check": "disk budget covers checkpoints and output buffer",
                "status": "passed" if report["disk_budget_gib"] >= report["recommended_disk_gib"] else "failed",
                "detail": "{:.2f} GiB >= {:.2f} GiB".format(
                    report["disk_budget_gib"],
                    report["recommended_disk_gib"],
                ),
            }
        )
    return rows


def build_session_budget_report(config_path=None):
    if not config_path:
        return {
            "status": "missing_budget_config",
            "summary": "No GPU session budget config was provided.",
            "config_path": None,
            "rows": [],
            "stop_rules": stop_rules(),
        }

    path = Path(config_path)
    if not path.exists():
        return {
            "status": "missing_budget_config",
            "summary": "GPU session budget config is missing: {}".format(path),
            "config_path": str(path),
            "rows": [],
            "stop_rules": stop_rules(),
        }

    config = load_json(path)
    missing, invalid = validate_config(config)
    profile = config.get("checkpoint_profile", "p01")
    currency = config.get("currency", "USD")

    if invalid:
        status = "invalid_budget_config"
        summary = "GPU session budget config contains invalid fields."
    elif missing:
        status = "incomplete_budget_config"
        summary = "GPU session budget config is incomplete."
    else:
        status = "budget_ready"
        summary = "GPU session budget is ready."

    report = {
        "status": status,
        "summary": summary,
        "config_path": str(path),
        "currency": currency,
        "gpu_provider": config.get("gpu_provider", ""),
        "gpu_name": config.get("gpu_name", ""),
        "checkpoint_profile": profile,
        "missing_fields": missing,
        "invalid_fields": invalid,
        "stop_policy": config.get("stop_policy", ""),
        "notes": config.get("notes", ""),
        "stop_rules": stop_rules(),
    }

    if missing or invalid:
        report["rows"] = build_budget_rows(report)
        return report

    gpu_hourly = float(config["gpu_hourly_usd"])
    overhead = float(config.get("billing_overhead_multiplier", 1.0))
    max_session_hours = float(config["max_session_hours"])
    max_budget = float(config["max_session_budget_usd"])
    disk_budget = float(config["disk_budget_gib"])
    output_buffer = float(config.get("output_buffer_gib", DEFAULT_OUTPUT_BUFFER_GIB))
    expected_gib = expected_checkpoint_gib(profile)
    recommended_disk = round(expected_gib + output_buffer, 2)
    estimated_cost = round(max_session_hours * gpu_hourly * overhead, 4)

    report.update(
        {
            "gpu_hourly_usd": gpu_hourly,
            "billing_overhead_multiplier": overhead,
            "max_session_hours": max_session_hours,
            "max_session_budget_usd": max_budget,
            "disk_budget_gib": disk_budget,
            "output_buffer_gib": output_buffer,
            "expected_checkpoint_gib": expected_gib,
            "recommended_disk_gib": recommended_disk,
            "estimated_session_cost_usd": estimated_cost,
            "budget_headroom_usd": round(max_budget - estimated_cost, 4),
        }
    )

    if estimated_cost > max_budget:
        report["status"] = "budget_exceeded"
        report["summary"] = "Estimated GPU session cost exceeds the configured cap."
    elif disk_budget < recommended_disk:
        report["status"] = "disk_budget_too_low"
        report["summary"] = "Configured disk budget is below the checkpoint footprint plus output buffer."

    report["rows"] = build_budget_rows(report)
    return report


def stop_rules():
    return [
        "Do not start the GPU session unless this report status is `budget_ready`.",
        "Verify the selected provider's current hourly price before filling `gpu_hourly_usd`.",
        "Set a provider-side spending cap or auto-shutdown at `max_session_hours` when the provider supports it.",
        "Run P01 first; do not upgrade to the required-suite profile until P01 acceptance passes and the budget is recalculated.",
        "After real runtime metrics are imported, use `docs/cost-review.json`; this budget guard is not a replacement for the final cost review.",
    ]


def markdown_budget_report(report):
    lines = [
        "# GPU Session Budget Guard",
        "",
        "- Status: `{}`".format(report["status"]),
        "- Summary: {}".format(report["summary"]),
        "- Config file: {}".format(report.get("config_path") or "-"),
    ]
    if report.get("checkpoint_profile"):
        lines.extend(
            [
                "- Provider: {}".format(report.get("gpu_provider") or "-"),
                "- GPU: {}".format(report.get("gpu_name") or "-"),
                "- Checkpoint profile: `{}`".format(report["checkpoint_profile"]),
                "- Stop policy: {}".format(report.get("stop_policy") or "-"),
            ]
        )
    if report.get("estimated_session_cost_usd") is not None:
        lines.extend(
            [
                "- GPU hourly cost: {:.4f} {}".format(report["gpu_hourly_usd"], report["currency"]),
                "- Billing overhead multiplier: {:.2f}".format(report["billing_overhead_multiplier"]),
                "- Max session hours: {:.2f}".format(report["max_session_hours"]),
                "- Estimated session cost: {:.4f} {}".format(report["estimated_session_cost_usd"], report["currency"]),
                "- Max session budget: {:.4f} {}".format(report["max_session_budget_usd"], report["currency"]),
                "- Budget headroom: {:.4f} {}".format(report["budget_headroom_usd"], report["currency"]),
                "- Expected checkpoint footprint: {:.2f} GiB".format(report["expected_checkpoint_gib"]),
                "- Recommended disk budget: {:.2f} GiB".format(report["recommended_disk_gib"]),
                "- Configured disk budget: {:.2f} GiB".format(report["disk_budget_gib"]),
            ]
        )
    if report.get("missing_fields") or report.get("invalid_fields"):
        lines.extend(
            [
                "- Missing fields: {}".format(", ".join(report.get("missing_fields", [])) or "-"),
                "- Invalid fields: {}".format(", ".join(report.get("invalid_fields", [])) or "-"),
            ]
        )

    lines.extend(["", "## Checks", "", "| Check | Status | Detail |", "| --- | --- | --- |"])
    if report.get("rows"):
        for row in report["rows"]:
            lines.append("| {} | `{}` | {} |".format(row["check"], row["status"], row["detail"]))
    else:
        lines.append("| budget config complete | `missing` | No config file was provided. |")

    lines.extend(["", "## Stop Rules", ""])
    lines.extend("- {}".format(rule) for rule in report["stop_rules"])
    return "\n".join(lines)


def write_json(data, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(text, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Create or validate a cloud GPU session budget before MagiHuman reproduction")
    parser.add_argument("--config")
    parser.add_argument("--profile", choices=sorted(PROFILE_GROUPS), default="p01")
    parser.add_argument("--create-template", action="store_true")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero unless the budget guard is ready.")
    args = parser.parse_args()

    if args.create_template:
        template = build_budget_template(profile=args.profile)
        text = json.dumps(template, ensure_ascii=False, indent=2)
        if args.output:
            write_json(template, args.output)
        print(text)
        return

    report = build_session_budget_report(args.config)
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else markdown_budget_report(report)
    if args.output:
        write_text(text, args.output)
    print(text)
    if args.strict and report["status"] != "budget_ready":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
