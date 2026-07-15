# Stage 46 Import Gap Report Refresh

## Purpose

Stage 46 connects the reproduction gap report to the GPU evidence import workflow.

After a returned `outputs/gpu-evidence-*.tar.gz` archive is safely imported, the workflow now regenerates:

- `docs/gpu-evidence-import-audit.md`
- `docs/mobile-feasibility-report.md`
- `docs/review-readiness.md`
- `docs/reproduction-gap-report.md`

This keeps the current "what is still missing?" report in sync with imported GPU evidence.

## Implementation

- Updated `backend/gpu_evidence_import_workflow.py`.
- The import workflow now calls `backend.reproduction_gap_report`.
- The import workflow Markdown summary includes `Reproduction gap status`.
- Invalid packages still do not import files and still do not generate a gap report update.

## Validation

Targeted validation passed:

```powershell
python -m unittest tests.test_gpu_evidence_import_workflow tests.test_reproduction_gap_report -v
```

The full local suite should pass 184 tests.

## Current State

No real GPU evidence package has been imported yet. The tracked gap report remains `awaiting_gpu_runtime`.
