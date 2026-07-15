# Stage 27: Model Audit Strict-Mode Ordering Fix

Date: 2026-07-16

Status: complete for local tooling

## Goal

Fix the execution order for checkpoint audits on a fresh GPU host.

Stage 25 added strict checkpoint audits, but the first integration made `DOWNLOAD_MODELS=1` run the initial pre-download model audit in strict mode. On a new GPU host, that would fail before the download step had a chance to create the model directories.

Stage 27 separates the two checks:

- pre-download model audit: report-only
- post-download model audit: strict
- direct execution without download: strict

## Files Changed

| File | Purpose |
| --- | --- |
| `scripts/run_p01_smoke_pipeline.sh` | Uses `INITIAL_MODEL_AUDIT_STRICT` so fresh-host downloads are not blocked before download |
| `scripts/gpu_reproduction_pipeline.sh` | Applies the same strict-mode ordering to the full required suite |
| `tests/test_pipeline_scripts.py` | Guards the intended download-before-strict-audit behavior |

## Correct Behavior

Fresh GPU host with download:

```bash
INSTALL_MAGICOMPILER=1 DOWNLOAD_MODELS=1 EXECUTE=1 bash scripts/run_p01_smoke_pipeline.sh
```

Expected order:

1. source preparation
2. strict preflight for commands, disk, and Hugging Face auth
3. non-strict model audit showing current missing/partial state
4. model download
5. strict post-download preflight
6. strict post-download model audit
7. P01 execution

Prepared GPU host without download:

```bash
EXECUTE=1 bash scripts/run_p01_smoke_pipeline.sh
```

Expected behavior:

- initial preflight requires existing models
- initial model audit is strict
- inference starts only if models are already complete enough

## Validation

Commands:

```powershell
python -m unittest tests.test_pipeline_scripts tests.test_model_audit tests.test_p01_smoke_pipeline -v
PREPARE_SOURCES=0 MIN_DISK_GIB=0 bash scripts/run_p01_smoke_pipeline.sh
```

Result:

```text
Ran 11 tests
OK
P01 dry-run reported missing models without blocking because EXECUTE=0.
```

## Next Step

Run the corrected P01 pipeline on a GPU host with `DOWNLOAD_MODELS=1`. The run should not stop at the pre-download model audit; it should stop only if Hugging Face auth/preflight fails, download fails, or the post-download model audit fails.
