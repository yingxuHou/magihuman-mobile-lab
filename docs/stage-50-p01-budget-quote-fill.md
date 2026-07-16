# Stage 50 P01 Budget Quote Fill

## Purpose

Stage 50 fills the pre-run GPU session budget with a current public quote and makes the first real P01 smoke run handoff-ready again.

This does not spend money and does not run inference. It records a bounded P01 candidate budget so the Linux NVIDIA GPU operator has an explicit cap before starting paid work.

## Quote

- Provider: Thunder Compute
- GPU: H100 PCIe 80GB
- Price source: https://www.thundercompute.com/pricing
- Price checked at: 2026-07-16
- Hourly price recorded: 2.19 USD / GPU hour

Re-check the provider price immediately before starting the paid session. Public cloud GPU prices can change.

## Budget

- Checkpoint profile: `p01`
- Max session hours: 4.0
- Billing overhead multiplier: 1.25
- Max session budget: 15.0 USD
- Estimated session cost: 10.95 USD
- Disk budget: 300.0 GiB
- Expected P01 checkpoint footprint: 114.64 GiB
- Recommended disk budget: 214.64 GiB

The budget guard status is now `budget_ready`.

## Implementation

- `backend.gpu_session_budget` now requires:
  - `gpu_provider`
  - `gpu_name`
  - `price_source_url`
  - `price_checked_at`
- Updated `docs/gpu-session-budget.json` with the quoted P01 budget.
- Regenerated:
  - `docs/gpu-session-budget-report.md`
  - `docs/gpu-session-budget-report.json`
  - `docs/gpu-execution-packet.md`
  - `docs/gpu-execution-packet.json`
  - `docs/reproduction-gap-report.md`
  - `docs/reproduction-gap-report.json`
- Updated the handoff packet so the local budget command validates the existing budget with `--strict` and does not recreate an empty template.

## Current State

- GPU session budget: `budget_ready`
- GPU execution packet: `ready_for_gpu_handoff`
- Reproduction gap report: `awaiting_gpu_runtime`
- Final mobile App recommendation: `B_pending_runtime`

## Next Step

Run the GPU execution packet on a Linux NVIDIA GPU host only after confirming the price is still current and setting the provider-side spending cap or shutdown rule.

Do not rerun `--create-template` unless intentionally replacing the budget file; it would overwrite the filled quote.

## Validation

Targeted validation:

```powershell
python -m unittest tests.test_gpu_session_budget tests.test_gpu_execution_packet tests.test_reproduction_gap_report -v
```

Full local validation:

```powershell
python -m unittest discover -s tests -v
```
