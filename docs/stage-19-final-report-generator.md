# Stage 19: Final Feasibility Report Generator

Date: 2026-07-16

Status: complete for local tooling

## Goal

Create a single report generator that combines all evidence gates used to decide whether daVinci-MagiHuman is suitable for a mobile app.

Before this stage, evidence existed in separate commands:

- runtime metrics summary
- mobile feasibility decision
- quality review
- cost review

Stage 19 creates one command that combines them into a tracked report.

## Files Changed

| File | Purpose |
| --- | --- |
| `backend/final_report.py` | Builds combined Markdown/JSON feasibility reports |
| `tests/test_final_report.py` | Tests incomplete runtime state, all-gates-passed state, stop candidate state, and Markdown sections |
| `scripts/final_report.ps1` | Windows launcher |
| `scripts/final_report.sh` | Linux launcher |
| `docs/mobile-feasibility-report.md` | Current generated report |
| `scripts/gpu_reproduction_pipeline.sh` | Writes timestamped final reports under `outputs/reports/` |

## Current Report

Command:

```powershell
python -m backend.final_report --log-dir logs --format markdown --output docs/mobile-feasibility-report.md
```

Current report status:

```text
Status: incomplete_runtime_evidence
Recommendation: B_pending_runtime
```

Evidence gates:

| Gate | Current Status |
| --- | --- |
| Static on-device feasibility | `not_viable` |
| Required GPU runtime metrics | `insufficient_runtime_evidence` |
| Generated sample quality | `missing_quality_review` |
| Cloud GPU cost and wait time | `missing_cost_review` |

## GPU Pipeline Integration

The GPU reproduction pipeline now writes:

```text
outputs/reports/final_report_<timestamp>.md
```

Run:

```bash
QUALITY_REVIEW=docs/quality-review.json \
COST_REVIEW=docs/cost-review.json \
EXECUTE=1 \
bash scripts/gpu_reproduction_pipeline.sh
```

## Validation

Command:

```powershell
python -m unittest tests.test_final_report -v
```

Result:

```text
Ran 5 tests
OK
```

## Next Step

After GPU metrics, quality review, and cost review exist, rerun the final report command and commit the updated `docs/mobile-feasibility-report.md`.
