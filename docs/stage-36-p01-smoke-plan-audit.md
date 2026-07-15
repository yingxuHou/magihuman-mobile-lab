# Stage 36: P01 Smoke Plan Audit

Date: 2026-07-16

Status: complete for local tooling and current P01 plan audit

## Goal

Before the first GPU execution, verify that the tracked P01 manifest matches the actual P01 pipeline plan. This prevents the project from generating runtime metrics with a prompt, seed, duration, result path, or manifest path that no longer matches `docs/p01-smoke-manifest.json`.

## What Changed

| File | Purpose |
| --- | --- |
| `backend/smoke_plan_audit.py` | Compares `docs/p01-smoke-manifest.json` against the current `backend.experiment_suite --cases P01` plan |
| `docs/p01-smoke-plan-audit.json` | Machine-readable current P01 plan audit |
| `docs/p01-smoke-plan-audit.md` | Human-readable current P01 plan audit |
| `scripts/run_p01_smoke_pipeline.sh` | Runs the smoke plan audit before download or execution |
| `backend/pipeline_artifact_audit.py` | Requires the P01 smoke plan audit artifacts in P01 artifact checks |
| `scripts/package_gpu_evidence.sh` | Includes `logs/*smoke_plan_audit*.json` in GPU evidence packages |
| `tests/test_smoke_plan_audit.py` | Covers ready state, result-dir mismatch, seed mismatch, Markdown output, and script packaging integration |

## Checks

The audit compares:

- manifest type
- P01 case id and name
- mode, resolution, and model variant
- duration seconds
- seed
- prompt SHA-256
- base and SR dimensions
- runner command
- expected result path
- `MAGIHUMAN_TASK_ID`
- `MAGIHUMAN_PROMPT`
- `MAGIHUMAN_MODE`
- `MAGIHUMAN_RESOLUTION`
- `MAGIHUMAN_DURATION_SECONDS`
- `MAGIHUMAN_SEED`
- `MAGIHUMAN_MODEL_VARIANT`
- `MAGIHUMAN_RESULT_PATH`
- `MAGIHUMAN_MANIFEST_PATH`

## Current Audit Result

`docs/p01-smoke-plan-audit.md` currently reports:

- Status: `ready`
- Result path: `outputs/smoke-test/P01.mp4`
- Seed: `42`
- Duration: `5`
- Resolution: `256p`
- Prompt SHA-256: `8c18770e93a979ecf1c1d8b3f9d7d62e829bb0353118c3a48534891938218222`

## Pipeline Behavior

The P01 smoke pipeline now runs:

```bash
python -m backend.smoke_plan_audit \
  --manifest docs/p01-smoke-manifest.json \
  --log-dir "$LOG_DIR" \
  --result-dir "$RESULT_DIR" \
  --strict
```

It writes:

- `logs/p01_smoke_plan_audit_<timestamp>.json`
- `outputs/reports/p01_smoke_plan_audit_<timestamp>.md`

If the manifest and generated plan diverge, the P01 pipeline stops before checkpoint download or GPU execution.

## Validation

```powershell
python -m unittest tests.test_smoke_plan_audit tests.test_pipeline_artifact_audit tests.test_p01_smoke_pipeline tests.test_evidence_package -v
python -m backend.smoke_plan_audit --format markdown --output docs/p01-smoke-plan-audit.md
python -m backend.smoke_plan_audit --format json --output docs/p01-smoke-plan-audit.json
```

Result:

- Targeted tests: 16 passed.
- Current P01 smoke plan audit: `ready`.

## Current Limit

This audit does not run inference. It only proves that the first P01 GPU run will use the same input contract currently tracked in the manifest. Runtime, video quality, mobile playback, and cost evidence remain pending.
