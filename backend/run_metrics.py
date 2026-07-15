import argparse
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path


def parse_number_with_unit(value):
    if value is None:
        return None
    text = str(value).strip()
    match = re.search(r"([-+]?\d+(?:\.\d+)?)", text)
    if not match:
        return None
    number = float(match.group(1))
    lowered = text.lower()
    if "gib" in lowered:
        return number * 1024.0
    if "gb" in lowered:
        return number * 1000.0
    return number


def parse_percent(value):
    number = parse_number_with_unit(value)
    return None if number is None else float(number)


def parse_int(value):
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def sha256_text(text):
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compact_dict(payload):
    return {key: value for key, value in payload.items() if value not in (None, "")}


def build_run_context(
    case_id=None,
    mode=None,
    resolution=None,
    variant=None,
    seed=None,
    target_duration_seconds=None,
    target_br_width=None,
    target_br_height=None,
    target_sr_width=None,
    target_sr_height=None,
    result_path=None,
    prompt=None,
    prompt_sha256=None,
    manifest_path=None,
):
    manifest_value = str(manifest_path) if manifest_path else None
    context = compact_dict(
        {
            "case_id": case_id,
            "mode": mode,
            "resolution": resolution,
            "variant": variant,
            "seed": parse_int(seed),
            "target_duration_seconds": parse_float(target_duration_seconds),
            "target_br_width": parse_int(target_br_width),
            "target_br_height": parse_int(target_br_height),
            "target_sr_width": parse_int(target_sr_width),
            "target_sr_height": parse_int(target_sr_height),
            "result_path": result_path,
            "prompt_sha256": prompt_sha256,
            "manifest_path": manifest_value,
        }
    )
    if prompt is not None:
        context["prompt_sha256"] = sha256_text(prompt)
        context["prompt_chars"] = len(prompt)
        context["prompt_preview"] = str(prompt)[:160].replace("\n", " ")
    if manifest_path:
        manifest = Path(manifest_path)
        context["manifest_exists"] = manifest.exists()
        if manifest.exists():
            context["manifest_sha256"] = sha256_file(manifest)
    return context


def parse_nvidia_smi_csv_text(text):
    rows = list(csv.DictReader(text.splitlines()))
    samples = []
    for row in rows:
        normalized = {key.strip().lower(): value.strip() if isinstance(value, str) else value for key, value in row.items()}
        sample = {
            "timestamp": normalized.get("timestamp"),
            "gpu_name": normalized.get("name"),
            "memory_used_mib": parse_number_with_unit(
                normalized.get("memory.used [mib]") or normalized.get("memory.used")
            ),
            "memory_total_mib": parse_number_with_unit(
                normalized.get("memory.total [mib]") or normalized.get("memory.total")
            ),
            "utilization_gpu_percent": parse_percent(
                normalized.get("utilization.gpu [%]") or normalized.get("utilization.gpu")
            ),
        }
        samples.append(sample)

    used = [sample["memory_used_mib"] for sample in samples if sample["memory_used_mib"] is not None]
    totals = [sample["memory_total_mib"] for sample in samples if sample["memory_total_mib"] is not None]
    utils = [sample["utilization_gpu_percent"] for sample in samples if sample["utilization_gpu_percent"] is not None]
    gpu_names = sorted({sample["gpu_name"] for sample in samples if sample["gpu_name"]})

    return {
        "samples": len(samples),
        "gpu_names": gpu_names,
        "peak_memory_used_mib": max(used) if used else None,
        "memory_total_mib": max(totals) if totals else None,
        "average_gpu_utilization_percent": sum(utils) / len(utils) if utils else None,
    }


def parse_nvidia_smi_csv(path):
    return parse_nvidia_smi_csv_text(Path(path).read_text(encoding="utf-8"))


def parse_elapsed_seconds(value):
    text = str(value).strip()
    pieces = text.split(":")
    if len(pieces) == 3:
        hours, minutes, seconds = pieces
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    if len(pieces) == 2:
        minutes, seconds = pieces
        return int(minutes) * 60 + float(seconds)
    return float(text)


def parse_time_v_text(text):
    metrics = {
        "wall_time_seconds": None,
        "max_resident_set_kbytes": None,
        "user_seconds": None,
        "system_seconds": None,
        "exit_status": None,
    }
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("Elapsed (wall clock) time"):
            match = re.search(r"(\d+:)?\d+:\d+(?:\.\d+)?|\d+(?:\.\d+)?$", stripped)
            if match:
                metrics["wall_time_seconds"] = parse_elapsed_seconds(match.group(0))
        elif stripped.startswith("Maximum resident set size"):
            metrics["max_resident_set_kbytes"] = int(stripped.rsplit(":", 1)[-1].strip())
        elif stripped.startswith("User time (seconds)"):
            metrics["user_seconds"] = float(stripped.rsplit(":", 1)[-1].strip())
        elif stripped.startswith("System time (seconds)"):
            metrics["system_seconds"] = float(stripped.rsplit(":", 1)[-1].strip())
        elif stripped.startswith("Exit status"):
            metrics["exit_status"] = int(stripped.rsplit(":", 1)[-1].strip())
    return metrics


def parse_time_v_log(path):
    return parse_time_v_text(Path(path).read_text(encoding="utf-8", errors="replace"))


def parse_ffprobe_json_text(text):
    payload = json.loads(text)
    streams = payload.get("streams", [])
    video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
    audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
    format_info = payload.get("format", {})

    duration = format_info.get("duration")
    if duration is None:
        for stream in streams:
            if stream.get("duration") is not None:
                duration = stream.get("duration")
                break

    first_video = video_streams[0] if video_streams else {}
    first_audio = audio_streams[0] if audio_streams else {}
    return {
        "duration_seconds": float(duration) if duration is not None else None,
        "has_video": bool(video_streams),
        "has_audio": bool(audio_streams),
        "video_stream_count": len(video_streams),
        "audio_stream_count": len(audio_streams),
        "width": first_video.get("width"),
        "height": first_video.get("height"),
        "video_codec_name": first_video.get("codec_name"),
        "video_profile": first_video.get("profile"),
        "video_pix_fmt": first_video.get("pix_fmt"),
        "video_bit_rate": parse_int(first_video.get("bit_rate")),
        "audio_codec_name": first_audio.get("codec_name"),
        "audio_sample_rate": parse_int(first_audio.get("sample_rate")),
        "audio_channels": parse_int(first_audio.get("channels")),
        "audio_bit_rate": parse_int(first_audio.get("bit_rate")),
        "format_name": format_info.get("format_name"),
        "size_bytes": int(format_info["size"]) if format_info.get("size") else None,
        "format_bit_rate": parse_int(format_info.get("bit_rate")),
    }


def ffprobe_video(path):
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(path),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return parse_ffprobe_json_text(completed.stdout)


def collect_metrics(log_path=None, smi_csv_path=None, video_path=None, run_context=None):
    result = {}
    if run_context:
        result["run"] = compact_dict(run_context)
    if log_path:
        result["time"] = parse_time_v_log(log_path)
    if smi_csv_path:
        result["gpu"] = parse_nvidia_smi_csv(smi_csv_path)
    if video_path:
        result["video"] = ffprobe_video(video_path)
    return result


def main():
    parser = argparse.ArgumentParser(description="Collect MagiHuman run metrics")
    parser.add_argument("--log")
    parser.add_argument("--smi-csv")
    parser.add_argument("--video")
    parser.add_argument("--output")
    parser.add_argument("--case-id")
    parser.add_argument("--mode")
    parser.add_argument("--resolution")
    parser.add_argument("--variant")
    parser.add_argument("--seed")
    parser.add_argument("--target-duration-seconds")
    parser.add_argument("--target-br-width")
    parser.add_argument("--target-br-height")
    parser.add_argument("--target-sr-width")
    parser.add_argument("--target-sr-height")
    parser.add_argument("--result-path")
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-sha256")
    parser.add_argument("--manifest")
    args = parser.parse_args()

    run_context = build_run_context(
        case_id=args.case_id,
        mode=args.mode,
        resolution=args.resolution,
        variant=args.variant,
        seed=args.seed,
        target_duration_seconds=args.target_duration_seconds,
        target_br_width=args.target_br_width,
        target_br_height=args.target_br_height,
        target_sr_width=args.target_sr_width,
        target_sr_height=args.target_sr_height,
        result_path=args.result_path,
        prompt=args.prompt,
        prompt_sha256=args.prompt_sha256,
        manifest_path=args.manifest,
    )
    metrics = collect_metrics(
        log_path=args.log,
        smi_csv_path=args.smi_csv,
        video_path=args.video,
        run_context=run_context,
    )
    body = json.dumps(metrics, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(body + "\n", encoding="utf-8")
    print(body)


if __name__ == "__main__":
    main()
