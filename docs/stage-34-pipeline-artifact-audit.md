# Stage 34: Pipeline Artifact Audit

Date: 2026-07-16

Status: local tooling complete; real GPU artifact audit still pending

## Goal

After a P01 or full GPU pipeline run, verify that the expected small evidence files were actually produced. This makes it easier to tell whether a GPU run is ready to package and import, instead of manually checking many timestamped logs and reports.

## What Changed

| File | Purpose |
| --- | --- |
| `backend/pipeline_artifact_audit.py` | Checks expected pipeline artifacts by run type, timestamp, log directory, report directory, and result directory |
| `scripts/run_p01_smoke_pipeline.sh` | Writes P01 artifact audit JSON/Markdown after the P01 summary reports |
| `scripts/gpu_reproduction_pipeline.sh` | Writes full-suite artifact audit JSON/Markdown after the full summary reports |
| `scripts/package_gpu_evidence.sh` | Includes `logs/*artifact_audit*.json` in the small GPU evidence package |
| `tests/test_pipeline_artifact_audit.py` | Covers P01 dry-run, P01 download/execute, full dry-run, missing artifacts, and script integration |

## P01 Audit

The P01 audit checks:

- preflight JSON and Markdown
- model audit JSON and Markdown
- smoke plan audit JSON and Markdown
- smoke plan shell script
- optional source preparation log
- optional Hugging Face access JSON and Markdown
- optional checkpoint download log
- optional download log audit JSON and Markdown
- optional post-download preflight and model audit reports
- execute log when `EXECUTE=1`
- P01 metrics JSON when `EXECUTE=1`
- `outputs/smoke-test/P01.mp4` when `EXECUTE=1`
- experiment summary, mobile video, feasibility decision, and final report Markdown

Pipeline outputs:

- `logs/p01_pipeline_artifact_audit_<timestamp>.json`
- `outputs/reports/p01_pipeline_artifact_audit_<timestamp>.md`

## Full-Suite Audit

The full audit checks:

- preflight JSON and Markdown
- model audit JSON and Markdown
- optional source preparation log
- optional Hugging Face access JSON and Markdown
- optional checkpoint download log
- optional download log audit JSON and Markdown
- optional post-download preflight and model audit reports
- dry-run shell script when `EXECUTE=0`
- suite execution log when `EXECUTE=1`
- metrics JSON and result MP4 for P01/P03/P04/T01/T02 when `EXECUTE=1`
- experiment summary, mobile video, feasibility decision, and final report Markdown

Pipeline outputs:

- `logs/pipeline_artifact_audit_<timestamp>.json`
- `outputs/reports/pipeline_artifact_audit_<timestamp>.md`

## Usage

Manual P01 audit:

```bash
python -m backend.pipeline_artifact_audit \
  --run p01 \
  --stamp "<timestamp>" \
  --log-dir logs \
  --report-dir outputs/reports \
  --result-dir outputs/smoke-test \
  --download-models \
  --execute \
  --format markdown
```

Manual full-suite audit:

```bash
python -m backend.pipeline_artifact_audit \
  --run full \
  --stamp "<timestamp>" \
  --log-dir logs \
  --report-dir outputs/reports \
  --result-dir outputs/experiment-results \
  --download-models \
  --execute \
  --format markdown
```

The P01 and full GPU pipelines run the matching audit automatically at the end of a successful pipeline.

## Validation

```powershell
python -m unittest tests.test_pipeline_artifact_audit tests.test_pipeline_scripts tests.test_p01_smoke_pipeline tests.test_evidence_package -v
bash -n scripts/run_p01_smoke_pipeline.sh
bash -n scripts/gpu_reproduction_pipeline.sh
bash -n scripts/package_gpu_evidence.sh
```

Results:

- Targeted Python tests: 14 passed.
- Bash syntax checks: passed.

## Current Limit

The audit proves only that expected files exist. It does not prove the model generated high-quality output, that the MP4 is mobile-ready, or that the cloud GPU cost is acceptable. Those decisions still depend on runtime metrics, mobile video checks, manual quality review, and cost review after the GPU run.
