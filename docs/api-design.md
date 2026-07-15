# API Design Notes

If on-device inference is not feasible, the fallback architecture is a mobile app that submits generation jobs to a GPU backend.

## Prototype Status

A minimal standard-library prototype has been added:

- `backend/api_server.py`
- `backend/task_store.py`
- `scripts/run_api_server.ps1`
- `scripts/run_api_server.sh`

It is intentionally dependency-free so it can run in the current local Python 3.8 environment. It does not run GPU inference. It validates the mobile-to-backend task contract and creates task records that a future GPU worker can consume.

## Draft Endpoints

- `POST /tasks`: create a generation task.
- `GET /tasks/{task_id}`: check status and progress.
- `GET /tasks/{task_id}/result`: fetch the generated video.
- `DELETE /tasks/{task_id}`: remove task assets.

## Implemented Endpoints

| Method | Path | Status |
| --- | --- | --- |
| `GET` | `/health` | Implemented |
| `POST` | `/tasks` | Implemented |
| `GET` | `/tasks` | Implemented |
| `GET` | `/tasks/{task_id}` | Implemented |
| `GET` | `/tasks/{task_id}/result` | Implemented; returns `404` until result exists |
| `DELETE` | `/tasks/{task_id}` | Implemented |

## Draft Task States

- `queued`
- `running`
- `succeeded`
- `failed`
- `canceled`

## Request Example

```bash
curl -X POST http://127.0.0.1:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A presenter says hello to the audience.",
    "language": "en",
    "mode": "t2v",
    "resolution": "256p",
    "duration_seconds": 5
  }'
```

## Response Shape

```json
{
  "id": "task-id",
  "state": "queued",
  "prompt": "A presenter says hello to the audience.",
  "language": "en",
  "mode": "t2v",
  "resolution": "256p",
  "duration_seconds": 5,
  "progress": 0,
  "error": null,
  "result_path": null,
  "worker": {
    "required": "gpu",
    "status": "not_started",
    "command_hint": "MODEL_ROOT=models bash scripts/magihuman_task_runner.sh"
  }
}
```

## Local Run

```powershell
python -m backend.api_server --host 127.0.0.1 --port 8080 --data-dir api_data
```

Or:

```powershell
.\scripts\run_api_server.ps1
```

## Test Command

```powershell
python -m unittest discover -s tests -v
```

Current result:

```text
Ran 18 tests
OK
```

## Queue Model

The prototype stores tasks in `api_data/tasks.json`, which is ignored by Git. A GPU worker can later poll for `queued` tasks, mark them `running`, call the MagiHuman inference script, write `result_path`, then mark the task `succeeded` or `failed`.

For a single GPU worker, use one active task at a time unless measured VRAM proves safe concurrency. For H100 production, the first implementation should still serialize jobs because MagiHuman is a large video generation model and compilation/cache warmup can cause transient memory spikes.

## Worker Prototype

Added:

- `backend/worker.py`
- `scripts/run_worker.ps1`
- `scripts/run_worker.sh`

The worker consumes one queued task at a time. It passes task metadata through environment variables:

- `MAGIHUMAN_TASK_ID`
- `MAGIHUMAN_PROMPT`
- `MAGIHUMAN_LANGUAGE`
- `MAGIHUMAN_MODE`
- `MAGIHUMAN_RESOLUTION`
- `MAGIHUMAN_DURATION_SECONDS`
- `MAGIHUMAN_RESULT_PATH`

The configured command must create the file at `MAGIHUMAN_RESULT_PATH`. If the command exits non-zero or does not create the file, the task is marked `failed`.

Example:

```powershell
python -m backend.worker `
  --data-dir api_data `
  --output-dir outputs/api-results `
  --command "MODEL_ROOT=models bash scripts/magihuman_task_runner.sh"
```

Current validation:

```text
Ran 18 tests in 1.969s
OK
```

## MagiHuman Runner

Added:

- `backend/magihuman_config.py`
- `scripts/magihuman_task_runner.sh`

The runner maps task fields to official daVinci-MagiHuman runtime parameters:

| Task resolution | Config template | Base size | SR size |
| --- | --- | --- | --- |
| `256p` | `example/base/config.json` | `448x256` | none |
| `540p` | `example/sr_540p/config.json` | `448x256` | `896x512` |
| `1080p` | `example/sr_1080p/config.json` | `448x256` | `1920x1088` |

The runner generates a config under `run_configs/`, calls `torchrun inference/pipeline/entry.py`, finds the generated mp4 for the output prefix, and copies it to `MAGIHUMAN_RESULT_PATH` for the API result endpoint.
