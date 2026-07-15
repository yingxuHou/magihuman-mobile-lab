# Stage 42: GPU Evidence Import Workflow

Date: 2026-07-16

## Goal

Make the local evidence-import step repeatable after a GPU host returns `outputs/gpu-evidence-*.tar.gz`.

The import workflow must avoid extracting arbitrary archive contents into the repository root, reject packages that contain generated videos or model weights, copy only small evidence files, and regenerate the import audit plus final mobile feasibility report.

## Implementation

- Added `backend/gpu_evidence_import_workflow.py`.
- Added `scripts/import_gpu_evidence_package.sh`.
- Added `scripts/import_gpu_evidence_package.ps1`.
- Added `tests/test_gpu_evidence_import_workflow.py`.

## Import Behavior

The workflow:

1. Opens the `.tar.gz` with path traversal checks.
2. Extracts it under `outputs/imported-gpu-evidence/`.
3. Locates the evidence package directory.
4. Rebuilds the package manifest and rejects forbidden suffixes such as `.mp4`, `.safetensors`, `.ckpt`, `.pt`, `.pth`, and `.onnx`.
5. Copies only:
   - `logs/*`
   - `docs/*`
   - `outputs/reports/*`
6. Regenerates:
   - `docs/gpu-evidence-import-audit.md`
   - `docs/mobile-feasibility-report.md`
   - `docs/gpu-evidence-import-workflow.md`

## Usage

PowerShell:

```powershell
.\scripts\import_gpu_evidence_package.ps1 -Archive outputs\gpu-evidence-<timestamp>.tar.gz
```

Bash:

```bash
bash scripts/import_gpu_evidence_package.sh outputs/gpu-evidence-<timestamp>.tar.gz
```

Use `--strict` only when the imported evidence is expected to be complete enough for a final update.

## Validation

Targeted validation passed:

```powershell
python -m unittest tests.test_gpu_evidence_import_workflow tests.test_evidence_import tests.test_evidence_package -v
bash -n scripts/import_gpu_evidence_package.sh
```

The targeted set contains 14 tests.
