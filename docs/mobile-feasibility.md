# Mobile Feasibility

This document will hold the final mobile app integration conclusion after reproduction data is collected.

## Current Status

The current statement is a hypothesis, not a final conclusion:

- Full on-device inference is unlikely because daVinci-MagiHuman is described as a 15B-parameter GPU-oriented video generation model.
- The likely product architecture is a mobile client connected to a GPU backend.
- Stage 00 added package-size evidence: the official model stack listed on Hugging Face is about 201.27 GiB before external models, and the base checkpoint group alone is about 28.54 GiB.

## Required Evidence

- Model weight size
- Peak VRAM
- 256p inference latency
- 1080p inference latency
- CUDA and NVIDIA GPU dependency
- Availability of ONNX, Core ML, NCNN, MNN, or other mobile export paths
- Output quality from reproduced samples

## Evidence Collected

| Date | Evidence | Impact |
| --- | --- | --- |
| 2026-07-15 | HF model stack is about 201.27 GiB across 56 files | Strong evidence against bundling the full model in a normal mobile app package |
| 2026-07-15 | Official README uses CUDA/PyTorch/MagiCompiler/Flash Attention and reports H100 performance | Strong evidence that normal mobile CPUs/NPUs are not the target runtime |
| 2026-07-15 | Current local machine has Intel Iris Xe only, no NVIDIA GPU/CUDA/Docker/Conda | Local machine cannot provide inference data; runtime measurements require a GPU server |
| 2026-07-15 | External required models add about 84.36 GiB, bringing the complete checkpoint estimate to about 285.63 GiB | Strong evidence that direct mobile packaging is not viable for the official stack |
| 2026-07-15 | Static source search found no ONNX/Core ML/NCNN/MNN/TFLite/TorchScript export path in the official daVinci-MagiHuman repo | Official stack has no visible mobile export workflow |
| 2026-07-15 | Local API prototype passed 6 tests for task creation, query, result lookup, and deletion | Cloud backend route is technically straightforward at the API layer, pending GPU worker execution |
| 2026-07-15 | Worker prototype passed local success/failure/no-queue tests; total backend tests now 9 | Cloud backend route now has a tested task execution skeleton, pending real GPU command integration |
| 2026-07-15 | Worker-compatible MagiHuman runner and config generator passed local tests; total backend tests now 13 | Cloud backend route can now call the official inference entry point once a GPU host and checkpoints are available |
| 2026-07-15 | Metrics parser passed local tests for `nvidia-smi`, `/usr/bin/time -v`, and `ffprobe` JSON; total backend tests now 18 | GPU run outputs can be converted into comparable data for the final mobile feasibility decision |
| 2026-07-15 | Experiment matrix for 256p, distill, 540p, 1080p, and multilingual TI2V passed local generation tests; total backend tests now 23 | GPU host now has an ordered test plan for quality, performance, and app feasibility evidence |
| 2026-07-15 | Experiment result aggregator passed local tests; total backend tests now 27 | Missing GPU evidence is now explicit and measurable in the final feasibility report |
| 2026-07-15 | Experiment runner with dependency checks passed local tests; total backend tests now 32 | GPU host can execute cases in the intended order and avoid invalid 1080p/multilingual runs before P01 passes |
| 2026-07-16 | Retry and result-retention cleanup policies passed local tests; total backend tests now 35 | Cloud backend route now covers common production mechanics: retry failed jobs and expire generated videos |
| 2026-07-16 | Feasibility decision generator passed local tests; current output is `B_pending_runtime` with missing required cases P01/P03/P04/T01/T02 | Official on-device stack is rejected by static evidence, while cloud backend remains pending real GPU measurements |
| 2026-07-16 | Required GPU experiment suite runner passed local tests; total backend tests now 43 | P01/P03/P04/T01/T02 can now be planned or executed as one ordered suite on the GPU host |
| 2026-07-16 | GPU preflight and reproduction pipeline passed local tests; total backend tests now 48 | GPU host execution now has a single auditable pipeline that produces preflight, results, and feasibility reports |
| 2026-07-16 | Quality review gate passed local tests; total backend tests now 55 | Runtime metrics alone are not enough; final cloud feasibility now requires structured sample review evidence |
| 2026-07-16 | Cost and wait-time review gate passed local tests; total backend tests now 64 | Final cloud feasibility now requires per-video cost and latency thresholds from the selected GPU provider |
| 2026-07-16 | Final feasibility report generator passed local tests; total backend tests now 69 | Static, runtime, quality, and cost evidence are now combined into one tracked report |
| 2026-07-16 | GPU evidence import audit passed local tests; total backend tests now 74 | GPU host evidence can now be packaged, imported, audited, and used to refresh the final report without committing videos or model weights |
| 2026-07-16 | GPU host bootstrap and source-locking tooling passed local tests; total backend tests now 79 | A fresh GPU host can now generate a preflight report, a Docker launcher, and verified source checkouts before running the required experiment suite |
| 2026-07-16 | GPU pipeline hardening passed local tests; total backend tests now 81 | The GPU run now fails early for missing Hugging Face auth, prepares official sources before preflight, and verifies model directories after download |
| 2026-07-16 | P01-only 256p smoke pipeline passed local dry-run and tests; total backend tests now 83 | The first GPU attempt can now run only the smallest required case before spending time on SR or multilingual cases |
| 2026-07-16 | Mobile video compatibility gate passed local tests; total backend tests now 90 | Final app feasibility now requires generated videos to be checked for MP4/H.264/AAC mobile playback compatibility or marked for transcoding |
| 2026-07-16 | Model checkpoint footprint audit passed local tests; total backend tests now 96 | GPU execution now fails early if required checkpoint groups are missing or obviously too small after download |
| 2026-07-16 | Evidence package manifest and import audit coverage passed local tests; total backend tests now 100 | GPU-host evidence handoff now includes preflight/model audit JSON and explicitly tracks missing mobile-video evidence |
| 2026-07-16 | Model audit strict-mode ordering fix passed local tests; total backend tests now 103 | Fresh GPU hosts can now download models before the strict post-download checkpoint audit blocks incomplete downloads |
| 2026-07-16 | Checkpoint download profiles passed local dry-run tests; total backend tests now 107 | P01 first-run downloads can avoid unnecessary distill/SR checkpoints before the smallest smoke test |
| 2026-07-16 | P01 smoke input manifest passed local tests; total backend tests now 109 | The first GPU run now has a tracked prompt, seed, duration, resolution, official source commit, and expected output path |
| 2026-07-16 | Metrics run-context metadata passed local tests; total backend tests now 112 | GPU metrics can now be matched to case id, seed, prompt hash, target duration/resolution, output path, and P01 manifest hash |
| 2026-07-16 | Metrics context audit passed local tests; total backend tests now 117 | Imported GPU evidence will be blocked if metrics lack run context or if P01 metrics do not match the smoke manifest |
| 2026-07-16 | Evidence package provenance passed local tests; total backend tests now 120 | Returned GPU evidence can now be traced to the project commit, official source commits, worktree dirty state, and P01 manifest hash |
| 2026-07-16 | Hugging Face access audit passed local tests; total backend tests now 126 | GPU-host downloads now verify token access to representative gated and public checkpoint files before transferring large model weights |
| 2026-07-16 | Pipeline artifact audit passed local tests; total backend tests now 131 | A successful GPU pipeline run now produces an explicit checklist proving expected logs, reports, metrics JSON, and result MP4 artifacts exist before evidence packaging |
| 2026-07-16 | Upstream drift audit passed local tests and live metadata check; total backend tests now 136 | The locked reproduction target still matches current official code/model/Space SHAs before the GPU run |

## Interim Position

Do not treat this as the final answer yet.

Current evidence is already enough to reject bundling the official full stack into a normal mobile app package. The remaining open question is whether a cloud GPU backend can meet latency, cost, and quality expectations for a mobile app.

## Current Recommendation

Use option B as the working product direction:

- Mobile app: account/session, prompt input, reference image upload, task status, video playback, save/share.
- Backend API: task creation, queue state, result delivery, deletion.
- GPU worker: daVinci-MagiHuman model loading and generation.
- Storage: uploaded inputs, logs, generated videos, expiration cleanup.

This recommendation still needs real GPU inference measurements before it becomes the final project conclusion.

## Repeatable Decision Command

Current command:

```powershell
python -m backend.feasibility_decision --log-dir logs --format markdown
```

Current output summary:

- A. Official on-device inference: `not_viable`
- B. Mobile app plus cloud GPU backend: `pending_runtime_evidence`
- C. Stop app productization: `not_decided`
- Recommendation: `B_pending_runtime`
- Missing required runtime cases: P01, P03, P04, T01, T02
- Missing quality review: P01, P03, P04, T01, T02
- Missing cost review: selected GPU hourly price, overhead multiplier, max cost per video, max wait time

## Required GPU Suite

Dry-run locally:

```powershell
python -m backend.experiment_suite --log-dir logs --format markdown
```

Execute on a prepared Linux NVIDIA GPU host:

```bash
bash scripts/run_experiment_suite.sh --execute
```

Full pipeline:

```bash
INSTALL_MAGICOMPILER=1 DOWNLOAD_MODELS=1 EXECUTE=1 bash scripts/gpu_reproduction_pipeline.sh
```

Fresh GPU host bootstrap:

```bash
export HF_TOKEN="<your_huggingface_token>"
bash scripts/bootstrap_gpu_host.sh
bash outputs/run_magi_container.sh
```

First GPU smoke case:

```bash
INSTALL_MAGICOMPILER=1 DOWNLOAD_MODELS=1 EXECUTE=1 bash scripts/run_p01_smoke_pipeline.sh
```

Mobile playback compatibility:

```powershell
python -m backend.mobile_video_check --log-dir logs --format markdown
```

Checkpoint footprint audit:

```powershell
python -m backend.model_audit --model-root models --profile p01 --format markdown
```

## Quality Review Gate

Create a review template after GPU samples exist:

```powershell
python -m backend.quality_review --create-template --output docs/quality-review.json
```

Summarize the review:

```powershell
python -m backend.quality_review --review docs/quality-review.json --format markdown
```

Use it in the decision:

```powershell
python -m backend.feasibility_decision --log-dir logs --quality-review docs/quality-review.json --format markdown
```

## Cost Review Gate

Create a cost review template:

```powershell
python -m backend.cost_review --create-template --output docs/cost-review.json
```

Summarize the review:

```powershell
python -m backend.cost_review --review docs/cost-review.json --log-dir logs --format markdown
```

Use both reviews in the decision:

```powershell
python -m backend.feasibility_decision --log-dir logs --quality-review docs/quality-review.json --cost-review docs/cost-review.json --format markdown
```

## Combined Report

Current tracked report:

- `docs/mobile-feasibility-report.md`
- `docs/gpu-evidence-import-audit.md`

Regenerate:

```powershell
python -m backend.final_report --log-dir logs --format markdown --output docs/mobile-feasibility-report.md
```

Audit imported GPU evidence:

```powershell
python -m backend.evidence_import --log-dir logs --final-report-output docs/mobile-feasibility-report.md --format markdown --output docs/gpu-evidence-import-audit.md
```
