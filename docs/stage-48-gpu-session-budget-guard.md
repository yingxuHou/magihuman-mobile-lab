# Stage 48 GPU Session Budget Guard

## Purpose

Stage 48 adds a pre-run budget guard for paid cloud GPU sessions.

The existing `backend.cost_review` gate evaluates real per-video cost after runtime metrics are collected. This stage adds a separate guard before renting or starting paid GPU time, so the first reproduction session has an explicit hourly price, session cap, disk budget, and stop policy.

## Outputs

- `backend/gpu_session_budget.py`
- `scripts/generate_gpu_session_budget.sh`
- `scripts/generate_gpu_session_budget.ps1`
- `docs/gpu-session-budget.json`
- `docs/gpu-session-budget-report.md`
- `docs/gpu-session-budget-report.json`

## Statuses

| Status | Meaning |
| --- | --- |
| `missing_budget_config` | No budget config was provided. |
| `incomplete_budget_config` | Required price, time, cost, or disk fields are missing. |
| `invalid_budget_config` | One or more fields are invalid. |
| `budget_exceeded` | Estimated session cost exceeds the configured cap. |
| `disk_budget_too_low` | Disk budget is below checkpoint footprint plus output buffer. |
| `budget_ready` | The session budget guard is ready. |

## Stage 48 State

At Stage 48, the tracked config was a template. The report status was `incomplete_budget_config` because no GPU provider, current hourly price, max session hours, max session budget, or disk budget had been selected yet.

This is intentional. Do not invent GPU prices from memory. Verify the provider's current price before filling `docs/gpu-session-budget.json`.

Stage 50 later fills a P01 smoke-run budget; the current tracked budget status is now `budget_ready`.

## Commands

Create or refresh the template:

```powershell
python -m backend.gpu_session_budget --create-template --output docs/gpu-session-budget.json
```

Generate the report:

```powershell
python -m backend.gpu_session_budget --config docs/gpu-session-budget.json --format markdown --output docs/gpu-session-budget-report.md
python -m backend.gpu_session_budget --config docs/gpu-session-budget.json --format json --output docs/gpu-session-budget-report.json
```

Block a GPU session unless the budget is ready:

```powershell
python -m backend.gpu_session_budget --config docs/gpu-session-budget.json --format markdown --output docs/gpu-session-budget-report.md --strict
```

## Handoff Packet

`backend.gpu_execution_packet` now includes a `Local Budget Guard` section. The GPU handoff still describes how to run the reproduction workflow, but the operator should complete the budget guard before renting or starting paid GPU time.

Stage 49 promotes this from guidance to a handoff gate: the GPU execution packet is `attention_required` until the budget guard status becomes `budget_ready`.

## Validation

Targeted validation:

```powershell
python -m unittest tests.test_gpu_session_budget tests.test_gpu_execution_packet -v
```

Full local validation:

```powershell
python -m unittest discover -s tests -v
```

## Limits

This budget guard does not prove mobile App feasibility. It only controls spend before the GPU reproduction session. Final cost evidence still requires imported runtime metrics and a completed `docs/cost-review.json`.
