import argparse
import json
import shlex
from pathlib import Path

from backend.experiment_results import build_summary, load_matrix
from backend.experiment_matrix import build_matrix
from backend.experiment_suite import REQUIRED_CASE_IDS
from backend.run_metrics import ffprobe_video


BROAD_MOBILE_VIDEO_CODECS = {"h264"}
BROAD_MOBILE_AUDIO_CODECS = {"aac"}
MOBILE_PIX_FMTS = {"yuv420p", "yuvj420p"}


def check_row(name, ok, required=True, detail="", remediation=None):
    return {
        "name": name,
        "ok": bool(ok),
        "required": required,
        "detail": detail,
        "remediation": remediation,
    }


def format_names(format_name):
    return {part.strip().lower() for part in str(format_name or "").split(",") if part.strip()}


def mb_from_bytes(size_bytes):
    return None if size_bytes is None else size_bytes / (1024 * 1024)


def transcode_command(input_path, output_path=None):
    input_path = str(input_path)
    output_path = output_path or str(Path(input_path).with_name(Path(input_path).stem + "_mobile.mp4"))
    return " ".join(
        [
            "ffmpeg",
            "-y",
            "-i",
            shlex.quote(input_path),
            "-c:v libx264",
            "-pix_fmt yuv420p",
            "-profile:v high",
            "-level 4.1",
            "-c:a aac",
            "-movflags +faststart",
            shlex.quote(str(output_path)),
        ]
    )


def evaluate_video_info(video, max_width=1920, max_height=1088, max_size_mb=100.0, require_audio=True):
    video = video or {}
    checks = []

    checks.append(
        check_row(
            "container_mp4",
            "mp4" in format_names(video.get("format_name")) or "mov" in format_names(video.get("format_name")),
            detail="format={}".format(video.get("format_name") or "unknown"),
            remediation="remux_or_transcode_to_mp4",
        )
    )
    checks.append(check_row("has_video", video.get("has_video") is True, detail=str(video.get("has_video"))))

    width = video.get("width")
    height = video.get("height")
    dimensions_ok = isinstance(width, int) and isinstance(height, int) and width <= max_width and height <= max_height
    checks.append(
        check_row(
            "dimensions",
            dimensions_ok,
            detail="{}x{}, max {}x{}".format(width or "?", height or "?", max_width, max_height),
        )
    )

    video_codec = str(video.get("video_codec_name") or "").lower()
    checks.append(
        check_row(
            "video_codec",
            video_codec in BROAD_MOBILE_VIDEO_CODECS,
            detail=video_codec or "missing",
            remediation="transcode_video_to_h264",
        )
    )

    pix_fmt = str(video.get("video_pix_fmt") or "").lower()
    checks.append(
        check_row(
            "pixel_format",
            pix_fmt in MOBILE_PIX_FMTS,
            detail=pix_fmt or "missing",
            remediation="transcode_to_yuv420p",
        )
    )

    has_audio = video.get("has_audio") is True
    checks.append(check_row("has_audio", has_audio, required=require_audio, detail=str(video.get("has_audio"))))
    audio_codec = str(video.get("audio_codec_name") or "").lower()
    checks.append(
        check_row(
            "audio_codec",
            (not require_audio and not has_audio) or audio_codec in BROAD_MOBILE_AUDIO_CODECS,
            required=require_audio,
            detail=audio_codec or "missing",
            remediation="transcode_audio_to_aac",
        )
    )

    size_mb = mb_from_bytes(video.get("size_bytes"))
    size_ok = size_mb is not None and size_mb <= max_size_mb
    checks.append(
        check_row(
            "file_size",
            size_ok,
            detail="{} MB, max {} MB".format("{:.2f}".format(size_mb) if size_mb is not None else "missing", max_size_mb),
        )
    )

    required_failures = [check for check in checks if check["required"] and not check["ok"]]
    transcode_failures = [
        check
        for check in required_failures
        if check.get("remediation") in {"remux_or_transcode_to_mp4", "transcode_video_to_h264", "transcode_to_yuv420p", "transcode_audio_to_aac"}
    ]
    if not required_failures:
        status = "mobile_video_ready"
    elif transcode_failures:
        status = "mobile_video_needs_transcode"
    else:
        status = "mobile_video_not_ready"

    return {
        "status": status,
        "video": video,
        "checks": checks,
        "required_failures": required_failures,
    }


def load_metrics(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def video_from_metrics(path):
    return load_metrics(path).get("video", {})


def build_single_report(metrics_path=None, video_path=None, **kwargs):
    if video_path:
        video = ffprobe_video(video_path)
        source = str(video_path)
        command = transcode_command(video_path)
    elif metrics_path:
        video = video_from_metrics(metrics_path)
        source = str(metrics_path)
        command = None
    else:
        video = {}
        source = None
        command = None
    evaluation = evaluate_video_info(video, **kwargs)
    return {
        "status": evaluation["status"],
        "source": source,
        "rows": [
            {
                "case_id": "-",
                "metrics_path": str(metrics_path) if metrics_path else None,
                "sample_path": str(video_path) if video_path else None,
                "status": evaluation["status"],
                "checks": evaluation["checks"],
                "required_failures": evaluation["required_failures"],
                "transcode_command": command if evaluation["status"] == "mobile_video_needs_transcode" else None,
            }
        ],
    }


def build_log_dir_report(log_dir="logs", case_ids=None, matrix=None, **kwargs):
    case_ids = case_ids or REQUIRED_CASE_IDS
    matrix = matrix or build_matrix()
    rows_by_id = {row["id"]: row for row in build_summary(matrix, log_dir=log_dir)}
    rows = []
    for case_id in case_ids:
        summary_row = rows_by_id.get(case_id, {"status": "missing_metrics", "metrics_path": None})
        metrics_path = summary_row.get("metrics_path")
        if summary_row.get("status") != "measured" or not metrics_path:
            rows.append(
                {
                    "case_id": case_id,
                    "metrics_path": metrics_path,
                    "sample_path": None,
                    "status": "missing_video_metrics",
                    "checks": [],
                    "required_failures": [],
                    "transcode_command": None,
                }
            )
            continue
        evaluation = evaluate_video_info(video_from_metrics(metrics_path), **kwargs)
        rows.append(
            {
                "case_id": case_id,
                "metrics_path": metrics_path,
                "sample_path": summary_row.get("result_path"),
                "status": evaluation["status"],
                "checks": evaluation["checks"],
                "required_failures": evaluation["required_failures"],
                "transcode_command": None,
            }
        )

    statuses = {row["status"] for row in rows}
    if statuses == {"mobile_video_ready"}:
        status = "mobile_video_ready"
    elif "mobile_video_needs_transcode" in statuses:
        status = "mobile_video_needs_transcode"
    elif "mobile_video_not_ready" in statuses:
        status = "mobile_video_not_ready"
    else:
        status = "missing_mobile_video_evidence"

    return {
        "status": status,
        "source": str(log_dir),
        "case_ids": list(case_ids),
        "rows": rows,
    }


def markdown_report(report):
    lines = [
        "# Mobile Video Compatibility",
        "",
        "- Status: `{}`".format(report["status"]),
        "- Source: {}".format(report.get("source") or "-"),
        "",
        "| Case | Status | Metrics | Failed checks | Transcode command |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report["rows"]:
        failures = ", ".join(check["name"] for check in row.get("required_failures", [])) or "-"
        command = row.get("transcode_command") or "-"
        lines.append(
            "| {case} | `{status}` | {metrics} | {failures} | {command} |".format(
                case=row["case_id"],
                status=row["status"],
                metrics=row.get("metrics_path") or "-",
                failures=failures,
                command=command,
            )
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Check generated videos for mobile playback compatibility")
    parser.add_argument("--log-dir")
    parser.add_argument("--cases", nargs="+")
    parser.add_argument("--matrix")
    parser.add_argument("--metrics")
    parser.add_argument("--video")
    parser.add_argument("--max-width", type=int, default=1920)
    parser.add_argument("--max-height", type=int, default=1088)
    parser.add_argument("--max-size-mb", type=float, default=100.0)
    parser.add_argument("--allow-missing-audio", action="store_true")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    args = parser.parse_args()

    kwargs = {
        "max_width": args.max_width,
        "max_height": args.max_height,
        "max_size_mb": args.max_size_mb,
        "require_audio": not args.allow_missing_audio,
    }
    if args.log_dir:
        matrix = load_matrix(args.matrix) if args.matrix else build_matrix()
        report = build_log_dir_report(log_dir=args.log_dir, case_ids=args.cases, matrix=matrix, **kwargs)
    else:
        report = build_single_report(metrics_path=args.metrics, video_path=args.video, **kwargs)

    text = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else markdown_report(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
