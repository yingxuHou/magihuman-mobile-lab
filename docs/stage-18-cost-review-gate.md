# Stage 18: Cost And Wait-Time Review Gate

Date: 2026-07-16

Status: complete for local tooling

## Goal

Add a cost and wait-time gate before the cloud GPU route can become a product recommendation.

The model may be technically runnable and visually acceptable, but a phone app still needs acceptable:

- cost per generated video
- user wait time
- billing overhead from warmup, idle time, retries, and queueing

## Files Changed

| File | Purpose |
| --- | --- |
| `backend/cost_review.py` | Creates cost review templates and summarizes per-case cost/latency thresholds |
| `tests/test_cost_review.py` | Tests missing config, incomplete config, passing review, failed review, and Markdown rendering |
| `backend/feasibility_decision.py` | Uses optional cost review evidence before advancing cloud route |
| `scripts/cost_review.ps1` | Windows launcher |
| `scripts/cost_review.sh` | Linux launcher |
| `docs/cost-review-rubric.md` | Cost formula and review commands |
| `scripts/gpu_reproduction_pipeline.sh` | Accepts `COST_REVIEW=<path>` for final feasibility decisions |

## Cost Review Template

Create a template:

```powershell
python -m backend.cost_review --create-template --output docs/cost-review.json
```

Required fields:

- `gpu_name`
- `gpu_hourly_usd`
- `billing_overhead_multiplier`
- `max_cost_per_video_usd`
- `max_wall_time_seconds`

Formula:

```text
cost_per_video = wall_time_seconds / 3600 * gpu_hourly_usd * billing_overhead_multiplier
```

## Feasibility Decision Integration

Current output still remains:

```text
Recommendation: B_pending_runtime
Runtime Evidence: missing P01/P03/P04/T01/T02
Quality Evidence: missing_quality_review
Cost Evidence: missing_cost_review
```

After GPU metrics and quality review exist:

- missing cost review -> `B_candidate_needs_cost_review`
- passing cost review -> `B_candidate_ready_for_product_review`
- failed cost review -> `C_candidate_cost_failed`

## GPU Pipeline Integration

After filling both review files:

```bash
QUALITY_REVIEW=docs/quality-review.json \
COST_REVIEW=docs/cost-review.json \
EXECUTE=1 \
bash scripts/gpu_reproduction_pipeline.sh
```

## Validation

Command:

```powershell
python -m unittest tests.test_cost_review tests.test_feasibility_decision -v
```

Result:

```text
Ran 14 tests
OK
```

## Next Step

Run the GPU suite, fill quality and cost review JSON files, then rerun the feasibility decision with both review files.
