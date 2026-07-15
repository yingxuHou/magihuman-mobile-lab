# GPU Execution Packet

- Status: `ready_for_gpu_handoff`
- Summary: GPU execution packet is ready for a Linux NVIDIA GPU operator.
- Local runtime status: `not_executed_on_this_workstation`
- Repository: https://github.com/yingxuHou/magihuman-mobile-lab.git
- Branch: `main`
- Docker image: `sandai/magi-human:latest`
- GPU execution provenance: recorded by `scripts/package_gpu_evidence.sh` on the GPU host
- P01 manifest SHA-256: `ab2b0ff85a2a130a6eb7b457a26d1bd7aa2546c1b2918b3317ea02f8e9ee0713`

## Handoff Checks

| Check | Status | Detail |
| --- | --- | --- |
| workflow readiness | ok | ready |
| P01 smoke manifest exists | ok | docs/p01-smoke-manifest.json |
| Git remote is known | ok | https://github.com/yingxuHou/magihuman-mobile-lab.git |
| GPU bootstrap script exists | ok | scripts/bootstrap_gpu_host.sh |
| GPU workflow script exists | ok | scripts/run_gpu_reproduction_workflow.sh |
| GPU evidence package script exists | ok | scripts/package_gpu_evidence.sh |
| local import PowerShell script exists | ok | scripts/import_gpu_evidence_package.ps1 |

## GPU Host Requirements

- Linux host with NVIDIA GPU visible to Docker
- Docker with NVIDIA Container Toolkit
- Hugging Face token with access to required gated model repositories
- At least 500 GiB free disk for required-suite checkpoints, caches, logs, and temporary outputs

## Fresh GPU Host Commands

```bash
git clone https://github.com/yingxuHou/magihuman-mobile-lab.git
cd magihuman-mobile-lab
git checkout main
export HF_TOKEN=<your_huggingface_token>
bash scripts/bootstrap_gpu_host.sh
bash outputs/run_magi_container.sh
```

## Container Commands

```bash
INSTALL_MAGICOMPILER=1 bash scripts/prepare_sources.sh
```
```bash
python -m backend.gpu_preflight --mode container --format markdown
```
```bash
PREPARE_SOURCES=0 INSTALL_MAGICOMPILER=1 RUN_P01=1 RUN_FULL=1 PACKAGE_EVIDENCE=1 P01_DOWNLOAD_MODELS=1 FULL_DOWNLOAD_MODELS=1 bash scripts/run_gpu_reproduction_workflow.sh
```

## Expected Artifacts

- `outputs/reports/gpu_reproduction_workflow_*.md`
- `outputs/reports/p01_acceptance_*.md`
- `outputs/reports/required_suite_acceptance_*.md`
- `docs/review-readiness.md`
- `outputs/gpu-evidence-*.tar.gz`
- `logs/*_metrics.json`
- `outputs/smoke-test/P01.mp4`
- `outputs/experiment-results/P03.mp4`
- `outputs/experiment-results/P04.mp4`
- `outputs/experiment-results/T01.mp4`
- `outputs/experiment-results/T02.mp4`

## Return Evidence

```bash
ls -lh outputs/gpu-evidence-*.tar.gz
cp outputs/gpu-evidence-*.tar.gz <local-machine-or-shared-storage>/
```

## Local Import

```powershell
.\scripts\import_gpu_evidence_package.ps1 -Archive outputs\gpu-evidence-<timestamp>.tar.gz
python -m backend.review_readiness --create-templates --format markdown --output docs\review-readiness.md
python -m backend.final_report --log-dir logs --quality-review docs\quality-review.json --cost-review docs\cost-review.json --format markdown --output docs\mobile-feasibility-report.md
```

## Decision Rule

Do not change the final mobile App recommendation until imported runtime evidence, quality review, cost review, and final report gates pass.
