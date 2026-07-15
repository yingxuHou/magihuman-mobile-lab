# Stage 29: P01 Smoke Input Manifest

Date: 2026-07-16

Status: complete for local tooling

## Goal

Lock the first real GPU run to one auditable P01 input contract before spending cloud GPU time.

P01 is the smallest required runtime case. It must be reproducible enough that the generated metrics, video, and later mobile playback checks can be traced back to the exact prompt, seed, resolution, duration, official source commit, config template, and expected output path.

## Files Changed

| File | Purpose |
| --- | --- |
| `backend/experiment_matrix.py` | Adds explicit `seed=42` to every planned experiment case and exports it as `MAGIHUMAN_SEED` |
| `scripts/magihuman_task_runner.sh` | Passes `--seed "${MAGIHUMAN_SEED:-42}"` to the official inference entrypoint |
| `backend/smoke_manifest.py` | Generates the P01 input manifest from the experiment matrix and official example files |
| `docs/p01-smoke-manifest.json` | Tracked JSON evidence for the P01 input contract |
| `docs/p01-smoke-manifest.md` | Human-readable P01 input summary |
| `docs/stage-05-smoke-test-readiness.md` | Updates the smoke-test input description to point at the manifest |
| `tests/test_smoke_manifest.py` | Verifies manifest generation and official/example parameter extraction |

## P01 Input Contract

| Field | Value |
| --- | --- |
| Case | `P01` |
| Mode | `t2v` |
| Resolution | `256p`, base `448x256` |
| Duration | 5 seconds |
| Seed | 42 |
| Variant | `base` |
| Prompt source | `backend.experiment_matrix` P01 prompt |
| Expected output | `outputs/smoke-test/P01.mp4` |
| Official source commit | `209209b7086eba2020c5439265221495a8357322` |

The official `example/base/run_T2V.sh` still uses 4 seconds and does not pass `--seed`. The project P01 case intentionally uses 5 seconds to match the todo acceptance target and now passes seed 42 explicitly.

P01 is T2V, so it does not consume `example/assets/image.png`. The manifest still records that image hash for later TI2V cases.

## Commands

Generate JSON:

```powershell
python -m backend.smoke_manifest --format json --output docs/p01-smoke-manifest.json
```

Generate Markdown:

```powershell
python -m backend.smoke_manifest --format markdown --output docs/p01-smoke-manifest.md
```

Run P01 on the GPU host:

```bash
INSTALL_MAGICOMPILER=1 DOWNLOAD_MODELS=1 EXECUTE=1 bash scripts/run_p01_smoke_pipeline.sh
```

## Validation

Commands:

```powershell
python -m unittest tests.test_smoke_manifest tests.test_experiment_matrix tests.test_experiment_runner -v
python -m unittest discover -s tests -v
python -m compileall backend tests
git diff --check
```

Result:

```text
Ran 109 tests
OK
```

## Next Step

Run the P01 smoke pipeline on a Linux NVIDIA GPU host. After it finishes, compare the generated `outputs/reports/p01_smoke_plan_*.sh` and `logs/*P01*_metrics.json` against `docs/p01-smoke-manifest.json`.
