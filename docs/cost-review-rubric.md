# Cost Review Rubric

Use this after GPU runtime metrics exist.

Create a cost review template:

```bash
python -m backend.cost_review --create-template --output docs/cost-review.json
```

Fill:

- `gpu_name`: the GPU used for the measured run
- `gpu_hourly_usd`: hourly price from the selected provider
- `billing_overhead_multiplier`: warmup, idle, queue, retry, and orchestration overhead
- `max_cost_per_video_usd`: product threshold for one generated video
- `max_wall_time_seconds`: product threshold for user wait time

Summarize:

```bash
python -m backend.cost_review --review docs/cost-review.json --log-dir logs --format markdown
```

Use it in the final decision:

```bash
python -m backend.feasibility_decision \
  --log-dir logs \
  --quality-review docs/quality-review.json \
  --cost-review docs/cost-review.json \
  --format markdown
```

## Formula

```text
cost_per_video = wall_time_seconds / 3600 * gpu_hourly_usd * billing_overhead_multiplier
```

The review passes only if every required case is within both thresholds:

- `cost_per_video <= max_cost_per_video_usd`
- `wall_time_seconds <= max_wall_time_seconds`

Required cases:

- P01
- P03
- P04
- T01
- T02

## Notes

Do not hard-code cloud prices in the repository. Use the actual selected provider price at the time of testing, then record it in `docs/cost-review.json`.
