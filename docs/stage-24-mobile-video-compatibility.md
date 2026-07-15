# Stage 24: Mobile Video Compatibility Gate

Date: 2026-07-16

Status: complete for local tooling, waiting for generated GPU samples

## Goal

Add a technical mobile playback gate to the final app feasibility decision.

Generating a video file is not enough for a mobile app. The output must also be deliverable in a format that phones can play, save, share, and preview reliably. Stage 24 adds a conservative MP4/H.264/AAC compatibility check based on `ffprobe` metadata captured in run metrics.

## Files Changed

| File | Purpose |
| --- | --- |
| `backend/run_metrics.py` | Preserves video/audio codec, pixel format, bitrate, and audio stream details from `ffprobe` |
| `backend/mobile_video_check.py` | Evaluates generated video metrics for mobile playback compatibility |
| `backend/final_report.py` | Adds mobile video compatibility to the combined final report |
| `tests/test_mobile_video_check.py` | Covers ready, transcode-needed, oversized, and missing-evidence states |
| `scripts/mobile_video_check.sh` | Linux launcher |
| `scripts/mobile_video_check.ps1` | Windows launcher |
| `scripts/gpu_reproduction_pipeline.sh` | Writes a mobile video compatibility report after runtime summary |
| `scripts/run_p01_smoke_pipeline.sh` | Writes a P01-specific mobile video compatibility report |
| `docs/mobile-feasibility-report.md` | Now includes a mobile video compatibility evidence gate |

## Compatibility Checks

The current conservative pass criteria are:

- container is MP4/MOV-compatible
- video stream exists
- dimensions are no larger than 1920 x 1088
- video codec is H.264
- pixel format is `yuv420p` or `yuvj420p`
- audio stream exists
- audio codec is AAC
- file size is no larger than 100 MB by default

If codec/container/pixel-format/audio checks fail, the report marks the video as `mobile_video_needs_transcode` and prints an `ffmpeg` command template.

## Commands

Check all required cases from imported metrics:

```powershell
python -m backend.mobile_video_check --log-dir logs --format markdown
```

Check only P01:

```powershell
python -m backend.mobile_video_check --log-dir logs --cases P01 --format markdown
```

Check a specific video directly:

```bash
python -m backend.mobile_video_check --video outputs/smoke-test/P01.mp4 --format markdown
```

## Final Report Impact

`docs/mobile-feasibility-report.md` now includes:

```text
Mobile video playback compatibility: missing_mobile_video_evidence
```

The status remains `incomplete_runtime_evidence` because no GPU runtime metrics exist yet. After runtime, quality, and cost gates pass, the final report will still withhold a ready-for-product status if generated videos need transcoding or lack mobile playback metadata.

## Validation

Commands:

```powershell
python -m unittest tests.test_mobile_video_check -v
python -m backend.mobile_video_check --log-dir logs --cases P01 --format markdown
```

Result:

```text
MobileVideoCheckTest: Ran 6 tests, OK
Current local status: missing_mobile_video_evidence
```

## Next Step

Run P01 on the GPU host, then use the generated metrics JSON to confirm whether `outputs/smoke-test/P01.mp4` is directly mobile-compatible or needs a delivery transcode.
