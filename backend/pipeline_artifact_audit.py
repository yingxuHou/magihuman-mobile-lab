import argparse
import json
from pathlib import Path


REQUIRED_FULL_CASES = ["P01", "P03", "P04", "T01", "T02"]


def exact_row(label, path, required=True):
    path = Path(path)
    ok = path.is_file()
    size_bytes = path.stat().st_size if ok else 0
    return {
        "label": label,
        "kind": "file",
        "target": str(path),
        "required": required,
        "ok": ok,
        "count": 1 if ok else 0,
        "size_bytes": size_bytes,
        "detail": "exists" if ok else "missing",
    }


def glob_row(label, root, pattern, required=True):
    root = Path(root)
    matches = sorted(path for path in root.glob(pattern) if path.is_file())
    ok = bool(matches)
    return {
        "label": label,
        "kind": "glob",
        "target": str(root / pattern),
        "required": required,
        "ok": ok,
        "count": len(matches),
        "size_bytes": sum(path.stat().st_size for path in matches),
        "matches": [str(path) for path in matches],
        "detail": "{} match(es)".format(len(matches)) if ok else "no matches",
    }


def add_common_reports(rows, report_dir, prefix, stamp):
    report_dir = Path(report_dir)
    rows.extend(
        [
            exact_row("experiment summary report", report_dir / "{}experiment_results_{}.md".format(prefix, stamp)),
            exact_row("mobile video report", report_dir / "{}mobile_video_check_{}.md".format(prefix, stamp)),
            exact_row("feasibility decision report", report_dir / "{}feasibility_decision_{}.md".format(prefix, stamp)),
            exact_row("final report", report_dir / "{}final_report_{}.md".format(prefix, stamp)),
        ]
    )


def build_p01_artifacts(
    stamp,
    log_dir="logs",
    report_dir="outputs/reports",
    result_dir="outputs/smoke-test",
    prepare_sources=False,
    download_models=False,
    hf_access_audit=True,
    execute=False,
):
    log_dir = Path(log_dir)
    report_dir = Path(report_dir)
    result_dir = Path(result_dir)
    rows = [
        exact_row("P01 preflight JSON", log_dir / "p01_preflight_{}.json".format(stamp)),
        exact_row("P01 preflight report", report_dir / "p01_preflight_{}.md".format(stamp)),
        exact_row("P01 model audit JSON", log_dir / "p01_model_audit_{}.json".format(stamp)),
        exact_row("P01 model audit report", report_dir / "p01_model_audit_{}.md".format(stamp)),
        exact_row("P01 smoke plan audit JSON", log_dir / "p01_smoke_plan_audit_{}.json".format(stamp)),
        exact_row("P01 smoke plan audit report", report_dir / "p01_smoke_plan_audit_{}.md".format(stamp)),
        exact_row("P01 smoke plan", report_dir / "p01_smoke_plan_{}.sh".format(stamp)),
    ]
    if prepare_sources:
        rows.append(exact_row("P01 source preparation log", log_dir / "p01_prepare_sources_{}.log".format(stamp)))
    if download_models:
        if hf_access_audit:
            rows.extend(
                [
                    exact_row("P01 Hugging Face access JSON", log_dir / "p01_hf_access_{}.json".format(stamp)),
                    exact_row("P01 Hugging Face access report", report_dir / "p01_hf_access_{}.md".format(stamp)),
                ]
            )
        rows.extend(
            [
                exact_row("P01 checkpoint download log", log_dir / "p01_download_models_{}.log".format(stamp)),
                exact_row("P01 post-download preflight JSON", log_dir / "p01_preflight_{}_post_download.json".format(stamp)),
                exact_row("P01 post-download preflight report", report_dir / "p01_preflight_{}_post_download.md".format(stamp)),
                exact_row("P01 post-download model audit JSON", log_dir / "p01_model_audit_{}_post_download.json".format(stamp)),
                exact_row("P01 post-download model audit report", report_dir / "p01_model_audit_{}_post_download.md".format(stamp)),
            ]
        )
    if execute:
        rows.extend(
            [
                exact_row("P01 execute log", log_dir / "p01_smoke_execute_{}.log".format(stamp)),
                glob_row("P01 metrics JSON", log_dir, "P01_*_metrics.json"),
                exact_row("P01 result mp4", result_dir / "P01.mp4"),
            ]
        )
    add_common_reports(rows, report_dir, "p01_", stamp)
    return rows


def build_full_artifacts(
    stamp,
    log_dir="logs",
    report_dir="outputs/reports",
    result_dir="outputs/experiment-results",
    prepare_sources=False,
    download_models=False,
    hf_access_audit=True,
    execute=False,
):
    log_dir = Path(log_dir)
    report_dir = Path(report_dir)
    result_dir = Path(result_dir)
    rows = [
        exact_row("full preflight JSON", log_dir / "gpu_preflight_{}.json".format(stamp)),
        exact_row("full preflight report", report_dir / "gpu_preflight_{}.md".format(stamp)),
        exact_row("full model audit JSON", log_dir / "model_audit_{}.json".format(stamp)),
        exact_row("full model audit report", report_dir / "model_audit_{}.md".format(stamp)),
    ]
    if prepare_sources:
        rows.append(exact_row("source preparation log", log_dir / "prepare_sources_{}.log".format(stamp)))
    if download_models:
        if hf_access_audit:
            rows.extend(
                [
                    exact_row("Hugging Face access JSON", log_dir / "hf_access_{}.json".format(stamp)),
                    exact_row("Hugging Face access report", report_dir / "hf_access_{}.md".format(stamp)),
                ]
            )
        rows.extend(
            [
                exact_row("checkpoint download log", log_dir / "download_models_{}.log".format(stamp)),
                exact_row("post-download preflight JSON", log_dir / "gpu_preflight_{}_post_download.json".format(stamp)),
                exact_row("post-download preflight report", report_dir / "gpu_preflight_{}_post_download.md".format(stamp)),
                exact_row("post-download model audit JSON", log_dir / "model_audit_{}_post_download.json".format(stamp)),
                exact_row("post-download model audit report", report_dir / "model_audit_{}_post_download.md".format(stamp)),
            ]
        )
    if execute:
        rows.append(exact_row("experiment suite execute log", log_dir / "experiment_suite_{}.log".format(stamp)))
        for case_id in REQUIRED_FULL_CASES:
            rows.append(glob_row("{} metrics JSON".format(case_id), log_dir, "{}_*_metrics.json".format(case_id)))
            rows.append(exact_row("{} result mp4".format(case_id), result_dir / "{}.mp4".format(case_id)))
    else:
        rows.append(exact_row("experiment suite dry-run script", log_dir / "experiment_suite_dryrun_{}.sh".format(stamp)))
    add_common_reports(rows, report_dir, "", stamp)
    return rows


def build_artifact_audit(
    run,
    stamp,
    log_dir="logs",
    report_dir="outputs/reports",
    result_dir=None,
    prepare_sources=False,
    download_models=False,
    hf_access_audit=True,
    execute=False,
):
    if run == "p01":
        rows = build_p01_artifacts(
            stamp,
            log_dir=log_dir,
            report_dir=report_dir,
            result_dir=result_dir or "outputs/smoke-test",
            prepare_sources=prepare_sources,
            download_models=download_models,
            hf_access_audit=hf_access_audit,
            execute=execute,
        )
    elif run == "full":
        rows = build_full_artifacts(
            stamp,
            log_dir=log_dir,
            report_dir=report_dir,
            result_dir=result_dir or "outputs/experiment-results",
            prepare_sources=prepare_sources,
            download_models=download_models,
            hf_access_audit=hf_access_audit,
            execute=execute,
        )
    else:
        raise ValueError("unknown pipeline artifact run: {}".format(run))
    failures = [row for row in rows if row["required"] and not row["ok"]]
    return {
        "status": "ready" if not failures else "not_ready",
        "run": run,
        "stamp": stamp,
        "log_dir": str(log_dir),
        "report_dir": str(report_dir),
        "result_dir": str(result_dir or ("outputs/smoke-test" if run == "p01" else "outputs/experiment-results")),
        "prepare_sources": prepare_sources,
        "download_models": download_models,
        "hf_access_audit": hf_access_audit,
        "execute": execute,
        "rows": rows,
        "failures": failures,
    }


def markdown_artifact_audit(report):
    lines = [
        "# Pipeline Artifact Audit",
        "",
        "- Status: `{}`".format(report["status"]),
        "- Run: `{}`".format(report["run"]),
        "- Stamp: `{}`".format(report["stamp"]),
        "- Execute: {}".format("yes" if report["execute"] else "no"),
        "- Download models: {}".format("yes" if report["download_models"] else "no"),
        "- Hugging Face access audit: {}".format("yes" if report["hf_access_audit"] else "no"),
        "",
        "| Artifact | Required | Status | Count | Target | Detail |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for row in report["rows"]:
        lines.append(
            "| {label} | {required} | {status} | {count} | `{target}` | {detail} |".format(
                label=row["label"],
                required="yes" if row["required"] else "no",
                status="ok" if row["ok"] else "missing",
                count=row["count"],
                target=row["target"],
                detail=row["detail"],
            )
        )
    return "\n".join(lines)


def write_output(text, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Audit expected artifacts from a MagiHuman GPU pipeline run")
    parser.add_argument("--run", choices=["p01", "full"], required=True)
    parser.add_argument("--stamp", required=True)
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--report-dir", default="outputs/reports")
    parser.add_argument("--result-dir")
    parser.add_argument("--prepare-sources", action="store_true")
    parser.add_argument("--download-models", action="store_true")
    parser.add_argument("--skip-hf-access-audit", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when any required artifact is missing.")
    args = parser.parse_args()

    report = build_artifact_audit(
        args.run,
        args.stamp,
        log_dir=args.log_dir,
        report_dir=args.report_dir,
        result_dir=args.result_dir,
        prepare_sources=args.prepare_sources,
        download_models=args.download_models,
        hf_access_audit=not args.skip_hf_access_audit,
        execute=args.execute,
    )
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else markdown_artifact_audit(report)
    if args.output:
        write_output(text, args.output)
    print(text)
    if args.strict and report["status"] != "ready":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
