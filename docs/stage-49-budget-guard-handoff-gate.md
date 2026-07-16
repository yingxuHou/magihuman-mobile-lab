# Stage 49 Budget Guard Handoff Gate

## Purpose

Stage 49 makes the GPU session budget guard a real handoff gate.

Stage 48 created the budget guard, but the GPU execution packet and reproduction gap report still treated the GPU handoff as ready. That was too weak: if the budget file is incomplete, the project should not start paid GPU time.

## Implementation

- `backend.gpu_execution_packet` now loads `docs/gpu-session-budget.json`.
- The packet adds a `GPU session budget guard` handoff check.
- The packet status becomes `attention_required` unless the budget guard status is `budget_ready`.
- The packet Markdown includes a `Budget Guard Status` section.
- `backend.reproduction_gap_report` now exposes `gpu_session_budget_status`.
- The gap report adds a `GPU session budget guard` gap while required-suite runtime evidence is still missing.
- Once required-suite runtime evidence exists, the budget guard no longer blocks review/cost/final-decision stages; it is a pre-run control, not a post-run cost review replacement.

## Stage 49 State

- GPU execution packet: `attention_required`
- GPU session budget: `incomplete_budget_config`
- Reproduction gap report: `handoff_not_ready`
- Final mobile App recommendation: `B_pending_runtime`

Stage 50 later filled a bounded P01 budget and returned the packet to `ready_for_gpu_handoff`. If the budget needs to be changed, fill `docs/gpu-session-budget.json` with a current provider price and spending cap, then rerun:

```powershell
python -m backend.gpu_session_budget --config docs/gpu-session-budget.json --format markdown --output docs/gpu-session-budget-report.md --strict
python -m backend.gpu_execution_packet --format markdown --output docs/gpu-execution-packet.md
python -m backend.reproduction_gap_report --format markdown --output docs/reproduction-gap-report.md
```

## Validation

Targeted validation:

```powershell
python -m unittest tests.test_gpu_execution_packet tests.test_reproduction_gap_report tests.test_gpu_session_budget -v
```

Full local validation:

```powershell
python -m unittest discover -s tests -v
```
