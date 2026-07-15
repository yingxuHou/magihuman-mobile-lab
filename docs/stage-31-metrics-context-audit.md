# Stage 31: Metrics Context Audit

Date: 2026-07-16

Status: complete for local tooling

## Goal

Prevent imported GPU metrics from being accepted unless they can be matched back to the planned experiment case and, for P01, the tracked smoke manifest.

Stage 30 made future metrics self-identifying. Stage 31 adds the audit that reads those fields and blocks final-report readiness when metrics are missing run context or when the context does not match the experiment matrix or P01 manifest.

## Files Changed

| File | Purpose |
| --- | --- |
| `backend/metrics_context_audit.py` | Audits `logs/*_metrics.json` run context against the experiment matrix and P01 manifest |
| `backend/evidence_import.py` | Includes metrics context audit in GPU evidence import readiness |
| `docs/gpu-evidence-import-audit.md` | Regenerated current audit with a Metrics Context Audit section |
| `tests/test_metrics_context_audit.py` | Covers matching P01 context, missing run context, seed mismatch, and Markdown output |
| `tests/test_evidence_import.py` | Verifies context mismatch blocks final update |

## Checks

For every metrics JSON that exists, the audit checks:

- `run.case_id`
- `run.mode`
- `run.resolution`
- `run.variant`
- `run.seed`
- `run.target_duration_seconds`
- `run.target_br_width`
- `run.target_br_height`
- `run.prompt_sha256`
- presence of `run.result_path`

For P01, it also checks against `docs/p01-smoke-manifest.json`:

- `run.manifest_path`
- `run.manifest_sha256`
- manifest expected result path
- manifest seed
- manifest target duration
- manifest base dimensions
- manifest prompt hash

## Commands

Run only the metrics context audit:

```powershell
python -m backend.metrics_context_audit --log-dir logs --format markdown
```

Run the full import audit:

```powershell
python -m backend.evidence_import --log-dir logs --final-report-output docs/mobile-feasibility-report.md --format markdown --output docs/gpu-evidence-import-audit.md
```

## Current Local Result

The current workstation still has no GPU metrics, so the context audit status is:

```text
missing_metrics
```

This is expected. After GPU evidence is imported, old metrics without a `run` section will be marked `missing_run_context`, and mismatched P01 seed/manifest fields will be marked `context_mismatch`.

## Validation

Commands:

```powershell
python -m unittest tests.test_metrics_context_audit tests.test_evidence_import tests.test_feasibility_decision -v
python -m unittest discover -s tests -v
python -m compileall backend tests
git diff --check
```

Result:

```text
Ran 117 tests
OK
```

## Next Step

After P01 runs on the GPU host, import the evidence package and rerun:

```powershell
python -m backend.evidence_import --log-dir logs --quality-review docs/quality-review.json --cost-review docs/cost-review.json --final-report-output docs/mobile-feasibility-report.md --format markdown --output docs/gpu-evidence-import-audit.md
```

The final report should not be updated until the metrics context audit is `context_ready` for the imported metrics.
