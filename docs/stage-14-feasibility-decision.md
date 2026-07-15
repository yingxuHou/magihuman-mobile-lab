# Stage 14: Mobile Feasibility Decision Generator

Date: 2026-07-16

Status: complete for local decision tooling

## Goal

Make the mobile-app conclusion repeatable instead of leaving it as a manual paragraph.

The new decision generator combines:

- static evidence from official source and model verification
- required GPU experiment status from `logs/*_metrics.json`
- the A/B/C decision format from `7.15-todolist.md`

## Files Changed

| File | Purpose |
| --- | --- |
| `backend/feasibility_decision.py` | Converts static and runtime evidence into A/B/C feasibility states |
| `tests/test_feasibility_decision.py` | Tests missing-metrics and measured-metrics decision behavior |
| `scripts/feasibility_decision.ps1` | Windows launcher |
| `scripts/feasibility_decision.sh` | Linux launcher |

## Current Decision Output

Command:

```powershell
python -m backend.feasibility_decision --log-dir logs --format markdown
```

Current result:

```text
Recommendation: B_pending_runtime
Official on-device inference: not_viable
Mobile app plus cloud GPU backend: pending_runtime_evidence
Stop app productization: not_decided
Missing required cases: P01, P03, P04, T01, T02
```

## Decision Rules

### A. Official On-Device Inference

Current status: `not_viable`

Evidence:

- complete checkpoint stack is about 285.63 GiB before cache, logs, and outputs
- base smoke-test dependency footprint is about 114.64 GiB
- official path uses PyTorch `torchrun`, CUDA/NCCL, MagiCompiler, and Flash Attention
- no official ONNX/Core ML/NCNN/MNN/TFLite/TorchScript export path was found in static source search

This is enough to reject bundling the official stack into a normal phone app.

### B. Mobile App Plus Cloud GPU Backend

Current status: `pending_runtime_evidence`

Evidence already prepared:

- API prototype
- queued worker prototype
- official runner integration
- metrics parser
- experiment matrix
- experiment case runner
- result aggregation
- retry and retention policies

Evidence still missing:

- P01 256p base T2V runtime metrics
- P03 540p SR runtime metrics
- P04 1080p SR runtime metrics
- T01 Mandarin TI2V runtime metrics
- T02 English TI2V runtime metrics
- output quality review on generated samples
- GPU cost per generated video

### C. Stop Productization

Current status: `not_decided`

Stopping the mobile product direction would be premature until the cloud GPU path has at least the required runtime metrics and quality review.

## Validation

Command:

```powershell
python -m unittest tests.test_feasibility_decision -v
```

Result:

```text
Ran 3 tests
OK
```

## Next Step

Run the required experiment cases on a Linux NVIDIA GPU host and place metrics JSON files under `logs/`. After that, rerun:

```powershell
python -m backend.feasibility_decision --log-dir logs --format markdown
```
