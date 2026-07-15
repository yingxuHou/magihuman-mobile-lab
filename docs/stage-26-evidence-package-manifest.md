# Stage 26: Evidence Package Manifest And Import Audit Coverage

Date: 2026-07-16

Status: complete for local tooling

## Goal

Keep the GPU evidence handoff complete and safe after adding new gates.

The project now produces more than metrics JSON: GPU preflight reports, model checkpoint audits, mobile video compatibility reports, final reports, and import audits. Stage 26 updates the evidence package so those small artifacts can be carried back from the GPU host without including model weights or generated videos.

## Files Changed

| File | Purpose |
| --- | --- |
| `backend/evidence_package.py` | Builds a manifest for packaged evidence and flags forbidden large/media/model files |
| `backend/evidence_provenance.py` | Records project/source commit provenance and P01 manifest hash |
| `tests/test_evidence_package.py` | Tests manifest creation and forbidden-file detection |
| `scripts/package_gpu_evidence.sh` | Copies preflight/model-audit JSON files, P01 manifest files, provenance files, and writes manifest JSON/Markdown |
| `backend/evidence_import.py` | Lists missing mobile video evidence in import audits |
| `tests/test_evidence_import.py` | Covers the new mobile-video missing-evidence path |
| `docs/gpu-evidence-import-audit.md` | Regenerated with mobile video missing evidence |

## Packaged Evidence

The package now includes:

- `logs/*_metrics.json`
- `logs/*preflight*.json`
- `logs/*model_audit*.json`
- `docs/quality-review.json`
- `docs/cost-review.json`
- `docs/mobile-feasibility-report.md`
- `docs/gpu-evidence-import-audit.md`
- `docs/p01-smoke-manifest.json`
- `docs/p01-smoke-manifest.md`
- `outputs/reports/*.md`
- `outputs/reports/*.json`
- `outputs/reports/*.log`
- `evidence-provenance.json`
- `evidence-provenance.md`
- `evidence-manifest.json`
- `evidence-manifest.md`

Forbidden artifact suffixes are rejected by the manifest strict check:

- video: `.mp4`, `.mov`, `.avi`, `.mkv`
- model/export weights: `.safetensors`, `.ckpt`, `.pt`, `.pth`, `.onnx`

## Validation

Commands:

```powershell
python -m unittest tests.test_evidence_package tests.test_evidence_provenance tests.test_evidence_import -v
PACKAGE_DIR=outputs/test-evidence-provenance ARCHIVE_PATH=outputs/test-evidence-provenance.tar.gz bash scripts/package_gpu_evidence.sh
```

Result:

```text
Ran 13 tests
OK
Evidence package manifest status: ok
Forbidden files: none
Evidence provenance generated: evidence-provenance.json and evidence-provenance.md
```

The temporary test package was deleted after verification.

## Import Audit Impact

`docs/gpu-evidence-import-audit.md` now reports missing mobile video evidence explicitly:

```text
mobile_video: P01, P03, P04, T01, T02
```

## Next Step

After the GPU host finishes P01 or the full suite, run:

```bash
bash scripts/package_gpu_evidence.sh
```

Then unpack the archive into the local repository and rerun:

```powershell
python -m backend.evidence_import --log-dir logs --quality-review docs/quality-review.json --cost-review docs/cost-review.json --final-report-output docs/mobile-feasibility-report.md --format markdown --output docs/gpu-evidence-import-audit.md
```
