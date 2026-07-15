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

## Required GPU Suite

Dry-run locally:

```powershell
python -m backend.experiment_suite --log-dir logs --format markdown
```

Execute on a prepared Linux NVIDIA GPU host:

```bash
bash scripts/run_experiment_suite.sh --execute
```
