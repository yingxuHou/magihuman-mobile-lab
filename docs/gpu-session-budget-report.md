# GPU Session Budget Guard

- Status: `incomplete_budget_config`
- Summary: GPU session budget config is incomplete.
- Config file: docs\gpu-session-budget.json
- Provider: -
- GPU: -
- Checkpoint profile: `p01`
- Stop policy: stop_before_download_if_over_budget
- Missing fields: gpu_hourly_usd, max_session_hours, max_session_budget_usd, disk_budget_gib
- Invalid fields: -

## Checks

| Check | Status | Detail |
| --- | --- | --- |
| budget config complete | `failed` | missing: gpu_hourly_usd, max_session_hours, max_session_budget_usd, disk_budget_gib; invalid: - |

## Stop Rules

- Do not start the GPU session unless this report status is `budget_ready`.
- Verify the selected provider's current hourly price before filling `gpu_hourly_usd`.
- Set a provider-side spending cap or auto-shutdown at `max_session_hours` when the provider supports it.
- Run P01 first; do not upgrade to the required-suite profile until P01 acceptance passes and the budget is recalculated.
- After real runtime metrics are imported, use `docs/cost-review.json`; this budget guard is not a replacement for the final cost review.
