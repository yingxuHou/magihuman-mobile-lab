# Stage 41: Workflow Readiness Audit

Date: 2026-07-16

## Goal

Before spending GPU time, statically verify that the end-to-end GPU reproduction workflow is still wired correctly.

This catches broken command chains before model download or inference starts.

## Implementation

- Added `backend/workflow_readiness_audit.py`.
- Integrated the audit into `scripts/run_gpu_reproduction_workflow.sh` before upstream drift audit and source preparation.
- Added `logs/*workflow_readiness*.json` to `scripts/package_gpu_evidence.sh`.
- Added `tests/test_workflow_readiness_audit.py`.
- Generated tracked local audit files:
  - `docs/gpu-workflow-readiness-audit.json`
  - `docs/gpu-workflow-readiness-audit.md`

## Checks

- Workflow script exists.
- Workflow runs upstream drift audit in strict mode.
- Workflow prepares locked sources.
- Workflow orders P01 before full suite before evidence packaging.
- Workflow forces P01 execution with `MODEL_PROFILE=p01`.
- Workflow forces full-suite execution with `MODEL_PROFILE=required_suite`.
- Workflow disables nested source preparation inside child pipelines.
- P01 pipeline has a strict P01 acceptance gate.
- Full pipeline has a strict required-suite acceptance gate.
- Evidence package includes P01 and required-suite acceptance JSON files.
- Bootstrap execute mode uses the workflow script.

## Current Local Result

Current tracked audit status: `ready`.

Manual command:

```bash
python -m backend.workflow_readiness_audit --format markdown --strict
```

## Validation

Targeted validation passed:

```powershell
python -m unittest tests.test_workflow_readiness_audit tests.test_gpu_reproduction_workflow tests.test_evidence_package -v
bash -n scripts/run_gpu_reproduction_workflow.sh
python -m backend.workflow_readiness_audit --format markdown --output docs/gpu-workflow-readiness-audit.md --strict
python -m backend.workflow_readiness_audit --format json --output docs/gpu-workflow-readiness-audit.json --strict
```

The targeted set contains 10 tests.
