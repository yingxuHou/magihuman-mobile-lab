# Stage 20: GPU Evidence Packaging And Import Audit

Date: 2026-07-16

Status: complete for local tooling

## Goal

Prepare the handoff from a GPU host back into the GitHub project.

The GPU host will generate logs, metrics, reports, and optionally review JSON files. Large videos and model weights must stay out of Git. Stage 20 adds:

- a packaging script for small GPU evidence files
- an import audit that checks whether the evidence package is complete enough to update the final report
- a metrics context audit that checks whether imported metrics match the planned case and P01 manifest
- a tracked current audit report showing what is still missing

## Files Changed

| File | Purpose |
| --- | --- |
| `backend/evidence_import.py` | Audits imported GPU evidence and final-report readiness |
| `backend/metrics_context_audit.py` | Audits metrics `run` context against the experiment matrix and P01 manifest |
| `tests/test_evidence_import.py` | Tests missing evidence, complete evidence, stop-candidate evidence, and Markdown rendering |
| `scripts/package_gpu_evidence.sh` | Packages metrics/reports/review JSON from a GPU host without videos or model weights |
| `scripts/evidence_import.ps1` | Windows import-audit launcher |
| `scripts/evidence_import.sh` | Linux import-audit launcher |
| `docs/gpu-evidence-import-audit.md` | Current tracked import audit |

## GPU Host Packaging

On the GPU host after running experiments and reviews:

```bash
bash scripts/package_gpu_evidence.sh
```

The package includes:

- `logs/*_metrics.json`
- `docs/quality-review.json`
- `docs/cost-review.json`
- `docs/mobile-feasibility-report.md`
- `outputs/reports/*.md`
- `outputs/reports/*.json`
- `outputs/reports/*.log`

It does not include model weights or video files.

## Local Import Audit

After unpacking the evidence package into the repository:

```powershell
python -m backend.evidence_import ^
  --log-dir logs ^
  --quality-review docs/quality-review.json ^
  --cost-review docs/cost-review.json ^
  --final-report-output docs/mobile-feasibility-report.md ^
  --format markdown ^
  --output docs/gpu-evidence-import-audit.md
```

Current local status:

```text
Status: incomplete_import
Recommendation: B_pending_runtime
```

Missing evidence:

- runtime metrics for P01, P03, P04, T01, T02
- quality review JSON
- cost review JSON
- mobile-video metrics for required cases

Metrics context status:

- `missing_metrics` on this workstation because no GPU runtime metrics have been imported yet
- after GPU import, metrics without a `run` section are rejected as `missing_run_context`
- P01 metrics with mismatched seed, prompt hash, duration, dimensions, result path, or manifest hash are rejected as `context_mismatch`

## Validation

Command:

```powershell
python -m unittest tests.test_evidence_import tests.test_metrics_context_audit -v
```

Result:

```text
Ran 12 tests
OK
```

## Next Step

Run the GPU suite, package the small evidence files, import them locally, rerun the import audit, and regenerate `docs/mobile-feasibility-report.md`.
