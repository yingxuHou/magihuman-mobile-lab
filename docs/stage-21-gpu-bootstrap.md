# Stage 21: GPU Host Bootstrap And Source Locking

Date: 2026-07-16

Status: complete for local tooling

## Goal

Make a fresh Linux NVIDIA GPU host reproducible without hand-copying the setup sequence.

Stage 21 adds a bootstrap layer that:

- generates the Docker launch command for the official `sandai/magi-human:latest` image
- locks the official daVinci-MagiHuman and MagiCompiler source commits
- clones or updates both source trees under ignored `third_party/`
- emits a host-side bootstrap report and a runnable container launcher
- keeps model weights, generated videos, and third-party repositories out of Git

## Files Changed

| File | Purpose |
| --- | --- |
| `backend/gpu_bootstrap.py` | Generates the GPU host/container bootstrap plan in Markdown, JSON, or shell form |
| `tests/test_gpu_bootstrap.py` | Tests Docker command generation, source commit locking, and output rendering |
| `scripts/prepare_sources.sh` | Clones or updates official source repositories at verified commits |
| `scripts/bootstrap_gpu_host.sh` | Runs host preflight, writes bootstrap reports, creates the container launcher, and optionally pulls/runs Docker |
| `docs/stage-21-gpu-bootstrap.md` | Records this stage |

## Locked Sources

| Source | Commit | Local path |
| --- | --- | --- |
| daVinci-MagiHuman | `209209b7086eba2020c5439265221495a8357322` | `third_party/daVinci-MagiHuman` |
| MagiCompiler | `bfef5bc70226a0c0740e4c551e4f7245a974fb4f` | `third_party/MagiCompiler` |

## GPU Host Bootstrap

On a fresh GPU host:

```bash
git clone https://github.com/yingxuHou/magihuman-mobile-lab.git
cd magihuman-mobile-lab
bash scripts/bootstrap_gpu_host.sh
```

This writes:

- `outputs/reports/gpu_host_preflight.md`
- `outputs/reports/gpu_bootstrap_plan.md`
- `outputs/run_magi_container.sh`

Start the container:

```bash
bash outputs/run_magi_container.sh
```

Inside the container:

```bash
INSTALL_MAGICOMPILER=1 bash scripts/prepare_sources.sh
DOWNLOAD_MODELS=1 EXECUTE=1 bash scripts/gpu_reproduction_pipeline.sh
bash scripts/package_gpu_evidence.sh
```

## Current Limitation

This stage does not run inference locally. The current Windows workstation still lacks NVIDIA GPU, CUDA, Docker, and Conda. The new value is that the cloud GPU host can now follow a locked and auditable setup path before running P01/P03/P04/T01/T02.

## Validation

Commands:

```powershell
python -m unittest tests.test_gpu_bootstrap -v
python -m backend.gpu_bootstrap --format markdown
```

Result:

```text
Ran 5 tests
OK
```

## Next Step

Run `bash scripts/bootstrap_gpu_host.sh` on a Linux NVIDIA GPU host, enter the generated container, execute the full GPU reproduction pipeline, then package and import the evidence.
