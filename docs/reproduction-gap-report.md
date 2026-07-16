# Reproduction Gap Report

- Status: `awaiting_gpu_runtime`
- Recommendation: `B_pending_runtime`
- Final report status: `incomplete_runtime_evidence`
- Required-suite acceptance: `not_ready`
- Review readiness: `runtime_not_ready`
- GPU execution packet: `ready_for_gpu_handoff`
- GPU session budget: `budget_ready`

## Evidence Gates

| Gate | Status |
| --- | --- |
| Static on-device feasibility | `not_viable` |
| Required GPU runtime metrics | `insufficient_runtime_evidence` |
| Generated sample quality | `missing_quality_review` |
| Cloud GPU cost and wait time | `missing_cost_review` |
| Mobile video playback compatibility | `missing_mobile_video_evidence` |

## Open Gaps

| Gate | Status | Detail | Next action |
| --- | --- | --- | --- |
| Required GPU runtime metrics | `missing` | Missing required cases: P01, P03, P04, T01, T02 | Run the GPU execution packet on a Linux NVIDIA GPU host and import the returned evidence package. |
| Required-suite acceptance | `not_ready` | Runtime, context, result MP4, duration, audio/video, or mobile playback checks are not complete. | Use `python -m backend.required_suite_acceptance --format markdown` after GPU evidence import. |
| Mobile video playback evidence | `missing` | Missing mobile playback metrics for: P01, P03, P04, T01, T02 | Collect ffprobe/video metadata from generated MP4 outputs and rerun mobile video checks. |
| Generated sample quality review | `missing_quality_review` | No quality review file was provided. | Create/fill `docs/quality-review.json` only after review readiness reports `review_inputs_ready`. |
| Cloud GPU cost and wait-time review | `missing_cost_review` | No cost review file was provided. | Fill `docs/cost-review.json` with GPU hourly price, overhead multiplier, max cost, and max wall time. |
| Review input readiness | `runtime_not_ready` | Required-suite runtime evidence is not ready; do not create or fill review inputs yet. | Do not fill quality/cost reviews until required-suite acceptance is ready. |

## Decision Rule

The final mobile App recommendation remains provisional until all required runtime, quality, cost, and mobile playback gaps are closed.
