# Stage 39: Required Suite Acceptance Gate

Date: 2026-07-16

## Goal

Decide whether the full required GPU suite has enough runtime evidence to proceed to quality review, cost review, and final mobile App feasibility judgment.

The required suite is `P01`, `P03`, `P04`, `T01`, and `T02`.

## Implementation

- Added `backend/required_suite_acceptance.py`.
- Integrated the gate into `scripts/gpu_reproduction_pipeline.sh` when `EXECUTE=1`.
- Added `logs/required_suite_acceptance_<timestamp>.json` and `outputs/reports/required_suite_acceptance_<timestamp>.md` to full pipeline artifact audit requirements.
- Added `logs/*required_suite_acceptance*.json` to the GPU evidence package.
- Updated full artifact audit so P01 result evidence can come from the P01 smoke output path `outputs/smoke-test/P01.mp4`.
- Added `tests/test_required_suite_acceptance.py`.

## Acceptance Statuses

| Status | Meaning | Next step |
| --- | --- | --- |
| `not_ready` | At least one required case is missing or inconsistent | Fix failed checks before quality/cost review |
| `ready_for_quality_and_cost_review` | Required runtime evidence passes | Create and fill quality/cost reviews |
| `ready_for_quality_and_cost_review_with_transcode_required` | Runtime evidence passes, but mobile delivery needs transcoding | Review may continue; final App plan must include transcoding |

## Checks Per Case

- Runtime metrics row is `measured`.
- Metrics context audit row is `context_ready`.
- Result MP4 exists.
- Video duration is close to the target duration, default tolerance +/- 1 second.
- Metrics report both video and audio.
- Mobile video check is either `mobile_video_ready` or `mobile_video_needs_transcode`.

## GPU Usage

The full pipeline writes:

```bash
logs/required_suite_acceptance_<timestamp>.json
outputs/reports/required_suite_acceptance_<timestamp>.md
```

Manual command:

```bash
python -m backend.required_suite_acceptance \
  --log-dir logs \
  --result-dir outputs/experiment-results \
  --p01-result-path outputs/smoke-test/P01.mp4 \
  --format markdown
```

Only start quality review and cost review when the status starts with `ready_for_quality_and_cost_review`.

## Validation

Targeted validation passed:

```powershell
python -m unittest tests.test_required_suite_acceptance tests.test_pipeline_artifact_audit tests.test_pipeline_scripts tests.test_evidence_package -v
bash -n scripts/gpu_reproduction_pipeline.sh
bash -n scripts/package_gpu_evidence.sh
```

The targeted set contains 18 tests.
