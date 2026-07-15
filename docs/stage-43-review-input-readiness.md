# Stage 43 Review Input Readiness

## Purpose

The project now has a gate between required-suite runtime acceptance and human review.

`backend.review_readiness` creates `docs/quality-review.json` and `docs/cost-review.json` only when `backend.required_suite_acceptance` reports a status that starts with `ready_for_quality_and_cost_review`.

## Commands

Generate the current readiness report:

```powershell
python -m backend.review_readiness --create-templates --format markdown --output docs/review-readiness.md
python -m backend.review_readiness --create-templates --format json --output docs/review-readiness.json
```

Wrapper scripts:

```bash
bash scripts/prepare_review_inputs.sh --format markdown --output docs/review-readiness.md
```

```powershell
.\scripts\prepare_review_inputs.ps1 --format markdown --output docs/review-readiness.md
```

## Current Result

- Status: `runtime_not_ready`
- Required-suite acceptance: `not_ready`
- Created review files: none

This is expected on the current workstation because no real GPU metrics, result MP4s, or mobile playback evidence have been imported.

## Integration

`scripts/gpu_reproduction_pipeline.sh` now runs review readiness after strict required-suite acceptance passes in `EXECUTE=1` mode.

`scripts/package_gpu_evidence.sh` now includes `docs/review-readiness.md` and `docs/review-readiness.json` when they exist.

`backend.gpu_evidence_import_workflow` now refreshes `docs/review-readiness.md` after a returned evidence archive is safely imported. If the imported evidence passes required-suite acceptance, the import workflow can create the quality and cost review templates automatically.

## Validation

Targeted validation passed:

```powershell
python -m unittest tests.test_review_readiness tests.test_required_suite_acceptance tests.test_quality_review tests.test_cost_review -v
python -m unittest tests.test_gpu_evidence_import_workflow tests.test_review_readiness -v
```

The full local suite should pass 173 tests.
