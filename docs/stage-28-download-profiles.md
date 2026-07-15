# Stage 28: Checkpoint Download Profiles

Date: 2026-07-16

Status: complete for local tooling

## Goal

Avoid downloading the complete 285 GiB checkpoint stack before the first P01 smoke test.

The first GPU run only needs the base 256p T2V path. Downloading distill and SR checkpoints before P01 wastes time, disk, and cloud GPU session budget. Stage 28 adds checkpoint download profiles:

- `p01`
- `required_suite`
- `complete`

## Files Changed

| File | Purpose |
| --- | --- |
| `scripts/download_models.sh` | Adds `MODEL_PROFILE` and `DRY_RUN` support |
| `scripts/run_p01_smoke_pipeline.sh` | Uses `MODEL_PROFILE=p01` by default when `DOWNLOAD_MODELS=1` |
| `scripts/gpu_reproduction_pipeline.sh` | Uses `MODEL_PROFILE=required_suite` by default when `DOWNLOAD_MODELS=1` |
| `tests/test_download_models_script.py` | Tests profile command generation in dry-run mode |
| `tests/test_pipeline_scripts.py` | Locks the P01 and full-pipeline default download profiles |

## Profiles

| Profile | Main daVinci groups | External models | Expected use |
| --- | --- | --- | --- |
| `p01` | `base/*`, `turbo_vae/*` | T5Gemma, Stable Audio, Wan VAE | First 256p P01 smoke run |
| `required_suite` | `base/*`, `turbo_vae/*`, `540p_sr/*`, `1080p_sr/*` | T5Gemma, Stable Audio, Wan VAE | P01/P03/P04/T01/T02 final-decision suite |
| `complete` | all daVinci groups | T5Gemma, Stable Audio, Wan VAE | Optional full local mirror, including distill |

`scripts/download_models.sh` keeps `MODEL_PROFILE=complete` as the default for backward compatibility. The P01 and full GPU pipelines override it with safer defaults.

## Commands

Dry-run P01 download commands:

```bash
MODEL_PROFILE=p01 DRY_RUN=1 bash scripts/download_models.sh
```

Download only P01-required checkpoints:

```bash
MODEL_PROFILE=p01 bash scripts/download_models.sh
```

Download the final-decision required suite:

```bash
MODEL_PROFILE=required_suite bash scripts/download_models.sh
```

Download everything:

```bash
MODEL_PROFILE=complete bash scripts/download_models.sh
```

## Pipeline Behavior

P01 smoke pipeline:

```bash
INSTALL_MAGICOMPILER=1 DOWNLOAD_MODELS=1 EXECUTE=1 bash scripts/run_p01_smoke_pipeline.sh
```

Uses:

```bash
MODEL_PROFILE=p01
```

Full GPU reproduction pipeline:

```bash
INSTALL_MAGICOMPILER=1 DOWNLOAD_MODELS=1 EXECUTE=1 bash scripts/gpu_reproduction_pipeline.sh
```

Uses:

```bash
MODEL_PROFILE=required_suite
```

## Validation

Commands:

```powershell
python -m unittest tests.test_download_models_script -v
MODEL_PROFILE=p01 DRY_RUN=1 bash scripts/download_models.sh
MODEL_PROFILE=required_suite DRY_RUN=1 bash scripts/download_models.sh
```

Result:

```text
Ran 4 tests
OK
P01 dry-run includes base/* and turbo_vae/*, not SR groups.
required_suite dry-run includes 540p_sr/* and 1080p_sr/*, not distill/*.
```

## Next Step

On the GPU host, use the P01 pipeline first. It will download the P01 profile, audit it, and only then run inference.
