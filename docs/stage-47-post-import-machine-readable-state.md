# Stage 47 Post-Import Machine-Readable State

## Purpose

Stage 47 makes the post-import state machine-readable after a GPU evidence archive is safely imported.

The import workflow already regenerated Markdown reports for human review. It now also refreshes JSON outputs so scripts, GitHub workflows, or future dashboards can inspect the current reproduction status without parsing Markdown.

## Outputs

After a safe import, `backend.gpu_evidence_import_workflow` now regenerates:

- `docs/review-readiness.md`
- `docs/review-readiness.json`
- `docs/reproduction-gap-report.md`
- `docs/reproduction-gap-report.json`

Invalid evidence packages still do not import files and still do not refresh these downstream reports.

## Implementation

- Added `--review-readiness-json-output` to `backend.gpu_evidence_import_workflow`.
- Added `--gap-report-json-output` to `backend.gpu_evidence_import_workflow`.
- The default import workflow writes both Markdown and JSON for review readiness and reproduction gap state.
- Integration tests now assert that the JSON files are written and that their statuses match the workflow summary.

## Validation

Targeted validation:

```powershell
python -m unittest tests.test_gpu_evidence_import_workflow tests.test_reproduction_gap_report tests.test_review_readiness -v
```

Full local validation:

```powershell
python -m unittest discover -s tests -v
```

## Current State

No real GPU evidence package has been imported yet. After Stage 49, the tracked gap report is `handoff_not_ready` until the GPU session budget guard is completed; the current recommendation remains `B_pending_runtime`.
