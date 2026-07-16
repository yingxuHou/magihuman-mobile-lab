# GPU Session Budget Guard

- Status: `budget_ready`
- Summary: GPU session budget is ready.
- Config file: docs\gpu-session-budget.json
- Provider: Thunder Compute
- GPU: H100 PCIe 80GB
- Region: provider_default
- Billing model: on_demand_gpu_hour
- Price source: https://www.thundercompute.com/pricing
- Price checked at: 2026-07-16
- Checkpoint profile: `p01`
- Stop policy: stop_before_download_if_over_budget
- GPU hourly cost: 2.1900 USD
- Billing overhead multiplier: 1.25
- Max session hours: 4.00
- Estimated session cost: 10.9500 USD
- Max session budget: 15.0000 USD
- Budget headroom: 4.0500 USD
- Expected checkpoint footprint: 114.64 GiB
- Recommended disk budget: 214.64 GiB
- Configured disk budget: 300.00 GiB

## Checks

| Check | Status | Detail |
| --- | --- | --- |
| budget config complete | `passed` | missing: -; invalid: - |
| estimated session cost within cap | `passed` | 10.9500 <= 15.0000 USD |
| disk budget covers checkpoints and output buffer | `passed` | 300.00 GiB >= 214.64 GiB |

## Stop Rules

- Do not start the GPU session unless this report status is `budget_ready`.
- Verify the selected provider's current hourly price before filling `gpu_hourly_usd`.
- Set a provider-side spending cap or auto-shutdown at `max_session_hours` when the provider supports it.
- Run P01 first; do not upgrade to the required-suite profile until P01 acceptance passes and the budget is recalculated.
- After real runtime metrics are imported, use `docs/cost-review.json`; this budget guard is not a replacement for the final cost review.
