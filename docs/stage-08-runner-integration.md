# Stage 08: MagiHuman Runner Integration

Date: 2026-07-15

Status: complete for local static integration and config tests

## Goal

Connect the tested API/worker task model to the official daVinci-MagiHuman runtime entry point.

This stage still does not execute GPU inference locally. It prepares the command bridge that should run on the GPU host.

## Files Added

| File | Purpose |
| --- | --- |
| `backend/magihuman_config.py` | Generates official config files with local checkpoint paths |
| `tests/test_magihuman_config.py` | Tests config generation for 256p and 1080p |
| `scripts/magihuman_task_runner.sh` | Worker-compatible Linux runner for official inference |

## Runtime Mapping

| Task field | Runner behavior |
| --- | --- |
| `MAGIHUMAN_PROMPT` | Passed to `--prompt` |
| `MAGIHUMAN_MODE=t2v` | Omits `--image_path` |
| `MAGIHUMAN_MODE=ti2v` | Passes `--image_path`; defaults to official sample image if missing |
| `MAGIHUMAN_RESOLUTION=256p` | Uses `example/base/config.json`, `448x256` |
| `MAGIHUMAN_RESOLUTION=540p` | Uses `example/sr_540p/config.json`, `448x256 -> 896x512` |
| `MAGIHUMAN_RESOLUTION=1080p` | Uses `example/sr_1080p/config.json`, `448x256 -> 1920x1088` |
| `MAGIHUMAN_RESULT_PATH` | Final mp4 is copied here for API download |

## Official Entry Point

The runner calls:

```bash
torchrun ${DISTRIBUTED_ARGS} inference/pipeline/entry.py
```

with:

- `--config-load-path`
- `--prompt`
- `--seconds`
- `--br_width`
- `--br_height`
- optional `--sr_width`
- optional `--sr_height`
- optional `--image_path`
- optional `--audio_path`
- `--output_path`

## Output Handling

The official pipeline appends runtime details to `--output_path`, so the runner:

1. creates an output prefix under `outputs/worker-runs`
2. runs official inference
3. searches for the generated mp4 matching that prefix
4. copies it to `MAGIHUMAN_RESULT_PATH`

This makes the API endpoint `GET /tasks/{task_id}/result` independent of official filename details.

## Validation

Command:

```powershell
python -m unittest discover -s tests -v
```

Result:

```text
Ran 13 tests in 2.001s
OK
```

Compile check:

```powershell
python -m compileall backend tests
```

Result: passed.

## Current Limitation

`scripts/magihuman_task_runner.sh` has not been executed locally because this machine does not have Linux bash, NVIDIA GPU, CUDA, Docker, Conda, checkpoints, or torch.

The next verification must happen on the GPU host.

## GPU Host Command

```bash
MAGIHUMAN_TASK_ID=manual-256p \
MAGIHUMAN_PROMPT="$(cat third_party/daVinci-MagiHuman/example/assets/prompt.txt)" \
MAGIHUMAN_MODE=t2v \
MAGIHUMAN_RESOLUTION=256p \
MAGIHUMAN_DURATION_SECONDS=5 \
MAGIHUMAN_RESULT_PATH="$PWD/outputs/smoke-test/manual-256p.mp4" \
MODEL_ROOT="$PWD/models" \
bash scripts/magihuman_task_runner.sh
```

## Next Step

Run Stage 08 on a GPU machine and record:

- generated mp4 path
- wall time
- peak VRAM
- command log
- `nvidia-smi` CSV
- output quality notes
