# Stage 06: API Prototype And Mobile Static Analysis

Date: 2026-07-15

Status: complete for local API prototype and static mobile-export inspection

## Goal

Continue mobile feasibility work while GPU inference is unavailable locally.

This stage answers two questions:

1. Does the official source expose an obvious mobile export path?
2. If direct mobile inference is not viable, what backend API contract should the phone use?

## Mobile Export Search

Searched official local clones for:

- ONNX
- Core ML
- NCNN
- MNN
- TFLite
- TensorFlow Lite
- TorchScript
- PyTorch mobile optimizer
- quantization / int8 export

Result:

- No official mobile export route was found in `GAIR-NLP/daVinci-MagiHuman`.
- No direct mobile export route was found in `SandAI-org/MagiCompiler`.
- The visible runtime path is PyTorch / torchrun / CUDA / NCCL / MagiCompiler / Flash Attention.
- Official SR scripts also use `CPU_OFFLOAD`, which reinforces that the target is a GPU server, not a phone.

## API Prototype

Added:

| File | Purpose |
| --- | --- |
| `backend/task_store.py` | Persistent JSON task store |
| `backend/api_server.py` | Dependency-free HTTP API |
| `tests/test_task_store.py` | Task store tests |
| `tests/test_api_server.py` | HTTP endpoint tests |
| `scripts/run_api_server.ps1` | Windows launcher |
| `scripts/run_api_server.sh` | Linux launcher |

The prototype is intentionally built on Python standard library modules so it can run on the current workstation without installing FastAPI or other packages.

## Implemented Endpoints

| Method | Path | Behavior |
| --- | --- | --- |
| `GET` | `/health` | health check |
| `POST` | `/tasks` | create queued generation task |
| `GET` | `/tasks` | list tasks |
| `GET` | `/tasks/{task_id}` | inspect task state |
| `GET` | `/tasks/{task_id}/result` | return generated file if present |
| `DELETE` | `/tasks/{task_id}` | delete task |

## Task States

Implemented states:

- `queued`
- `running`
- `succeeded`
- `failed`
- `canceled`

The prototype does not run daVinci-MagiHuman itself. It records a `worker.command_hint` so a future GPU worker can consume queued tasks and call the correct inference script.

## Validation

Command:

```powershell
python -m unittest discover -s tests -v
```

Result:

```text
Ran 6 tests in 1.193s
OK
```

Compile check:

```powershell
python -m compileall backend tests
```

Result: passed.

## Impact On App Feasibility

The current evidence supports this working direction:

- Do not package the official model into the phone app.
- Use the phone as a client for task creation and result playback.
- Run inference on a GPU backend.
- Start with single-task-per-GPU scheduling until real VRAM measurements prove safe concurrency.

Still missing:

- Real 256p inference latency.
- Real 256p peak VRAM.
- Real 1080p inference latency.
- Real 1080p peak VRAM.
- Output quality review from generated samples.

## Next Step

When a GPU host is available:

1. Run `scripts/cloud_env_check.sh`.
2. Download checkpoints.
3. Run `scripts/magihuman_task_runner.sh`.
4. Connect the API task store to a real GPU worker.
