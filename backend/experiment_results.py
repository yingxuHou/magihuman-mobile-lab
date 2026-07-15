import argparse
import json
from pathlib import Path

from backend.experiment_matrix import build_matrix


def load_matrix(path=None):
    if path and Path(path).exists():
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return build_matrix()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def latest_metrics_path(log_dir, case_id):
    log_dir = Path(log_dir)
    matches = sorted(log_dir.glob("{}_*_metrics.json".format(case_id)))
    return matches[-1] if matches else None


def summarize_metrics(metrics):
    time = metrics.get("time", {})
    gpu = metrics.get("gpu", {})
    video = metrics.get("video", {})
    return {
        "wall_time_seconds": time.get("wall_time_seconds"),
        "peak_memory_used_mib": gpu.get("peak_memory_used_mib"),
        "memory_total_mib": gpu.get("memory_total_mib"),
        "gpu_names": ", ".join(gpu.get("gpu_names", [])) if gpu.get("gpu_names") else None,
        "video_duration_seconds": video.get("duration_seconds"),
        "video_width": video.get("width"),
        "video_height": video.get("height"),
        "has_audio": video.get("has_audio"),
        "has_video": video.get("has_video"),
        "size_bytes": video.get("size_bytes"),
    }


def build_summary(matrix=None, log_dir="logs"):
    matrix = matrix or build_matrix()
    rows = []
    for case in matrix:
        metrics_path = latest_metrics_path(log_dir, case["id"])
        row = {
            "id": case["id"],
            "name": case["name"],
            "category": case["category"],
            "language": case["language"],
            "mode": case["mode"],
            "resolution": case["resolution"],
            "variant": case["variant"],
            "required": case["required"],
            "status": "missing_metrics",
            "metrics_path": str(metrics_path) if metrics_path else None,
        }
        if metrics_path:
            row.update(summarize_metrics(load_json(metrics_path)))
            if row.get("has_video") and row.get("has_audio") and row.get("wall_time_seconds") is not None:
                row["status"] = "measured"
            else:
                row["status"] = "incomplete_metrics"
        rows.append(row)
    return rows


def required_missing(rows):
    return [row["id"] for row in rows if row["required"] and row["status"] != "measured"]


def feasibility_state(rows):
    missing = required_missing(rows)
    p01 = next((row for row in rows if row["id"] == "P01"), None)
    p04 = next((row for row in rows if row["id"] == "P04"), None)

    if missing:
        return {
            "state": "insufficient_runtime_evidence",
            "summary": "Required GPU metrics are missing: {}".format(", ".join(missing)),
        }

    if p01 and p04:
        return {
            "state": "cloud_runtime_measured",
            "summary": "Required GPU metrics exist; compare latency/cost/quality before product decision.",
        }

    return {
        "state": "incomplete",
        "summary": "Experiment summary is incomplete.",
    }


def markdown_summary(rows):
    lines = [
        "| ID | Status | Resolution | Mode | GPU | Wall time (s) | Peak VRAM (MiB) | Video | Audio | Metrics |",
        "| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for row in rows:
        video_shape = "-"
        if row.get("video_width") and row.get("video_height"):
            video_shape = "{}x{}".format(row["video_width"], row["video_height"])
        lines.append(
            "| {id} | {status} | {resolution} | {mode} | {gpu} | {wall} | {vram} | {video} | {audio} | {metrics} |".format(
                id=row["id"],
                status=row["status"],
                resolution=row["resolution"],
                mode=row["mode"],
                gpu=row.get("gpu_names") or "-",
                wall="{:.2f}".format(row["wall_time_seconds"]) if row.get("wall_time_seconds") is not None else "-",
                vram="{:.0f}".format(row["peak_memory_used_mib"]) if row.get("peak_memory_used_mib") is not None else "-",
                video=video_shape,
                audio="yes" if row.get("has_audio") else ("no" if row.get("has_audio") is False else "-"),
                metrics=row.get("metrics_path") or "-",
            )
        )
    return "\n".join(lines)


def build_report(matrix_path=None, log_dir="logs"):
    rows = build_summary(load_matrix(matrix_path), log_dir)
    state = feasibility_state(rows)
    return {
        "state": state,
        "rows": rows,
        "markdown": markdown_summary(rows),
    }


def main():
    parser = argparse.ArgumentParser(description="Summarize MagiHuman experiment results")
    parser.add_argument("--matrix")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--output")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()

    report = build_report(matrix_path=args.matrix, log_dir=args.log_dir)
    body = report["markdown"] if args.format == "markdown" else json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(body + "\n", encoding="utf-8")
    print(body)


if __name__ == "__main__":
    main()

