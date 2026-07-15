# Stage 38: P01 Smoke Acceptance Gate

Date: 2026-07-16

## Goal

Decide whether the first real P01 GPU smoke run is strong enough evidence to continue into the full required suite.

P01 cannot pass only because an MP4 file exists. It must also have measured metrics, matching run context, expected duration, audio/video streams, and mobile playback evidence.

## Implementation

- Added `backend/p01_acceptance.py`.
- Integrated the gate into `scripts/run_p01_smoke_pipeline.sh` when `EXECUTE=1`.
- Added `logs/p01_acceptance_<timestamp>.json` and `outputs/reports/p01_acceptance_<timestamp>.md` to P01 artifact audit requirements.
- Added `logs/*p01_acceptance*.json` to the GPU evidence package.
- Added `tests/test_p01_acceptance.py`.

## Acceptance Statuses

| Status | Meaning | Next step |
| --- | --- | --- |
| `not_ready` | P01 evidence is incomplete or inconsistent | Fix failed checks before full suite |
| `ready_for_full_suite` | P01 metrics/context/video evidence passes | Run P03/P04/T01/T02 |
| `ready_for_full_suite_with_transcode_required` | P01 inference evidence passes, but the generated video needs mobile delivery transcoding | Full suite may run; final app feasibility must include a transcode path |

## Checks

- Runtime metrics row for P01 is `measured`.
- P01 metrics context audit row is `context_ready`.
- `outputs/smoke-test/P01.mp4` exists.
- Video duration is close to 5 seconds, default tolerance +/- 1 second.
- Metrics report both video and audio.
- Mobile video check is either `mobile_video_ready` or `mobile_video_needs_transcode`.

## GPU Usage

After the P01 pipeline finishes on the GPU host, inspect:

```bash
cat outputs/reports/p01_acceptance_<timestamp>.md
```

Manual command:

```bash
python -m backend.p01_acceptance \
  --log-dir logs \
  --result-path outputs/smoke-test/P01.mp4 \
  --format markdown
```

Only run the full suite when the status starts with `ready_for_full_suite`.

## Validation

Targeted validation passed:

```powershell
python -m unittest tests.test_p01_acceptance tests.test_pipeline_artifact_audit tests.test_p01_smoke_pipeline tests.test_evidence_package -v
bash -n scripts/run_p01_smoke_pipeline.sh
bash -n scripts/package_gpu_evidence.sh
```

The targeted set contains 16 tests.
