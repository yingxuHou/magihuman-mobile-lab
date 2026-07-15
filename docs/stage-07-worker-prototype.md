# Stage 07: Worker Prototype

Date: 2026-07-15

Status: complete for local worker skeleton

## Goal

Add the missing backend execution layer between the mobile API and the future GPU inference command.

The worker prototype should:

- consume queued tasks
- mark tasks `running`
- execute one configured command
- pass task metadata through environment variables
- mark tasks `succeeded` when a result file appears
- mark tasks `failed` when the command fails or no result is produced

## Files Added

| File | Purpose |
| --- | --- |
| `backend/worker.py` | Single-task worker executor |
| `tests/test_worker.py` | Worker success/failure/no-queue tests |
| `scripts/run_worker.ps1` | Windows launcher |
| `scripts/run_worker.sh` | Linux launcher |

## Worker Contract

The worker receives a command template and sets these environment variables:

- `MAGIHUMAN_TASK_ID`
- `MAGIHUMAN_PROMPT`
- `MAGIHUMAN_LANGUAGE`
- `MAGIHUMAN_MODE`
- `MAGIHUMAN_RESOLUTION`
- `MAGIHUMAN_DURATION_SECONDS`
- `MAGIHUMAN_RESULT_PATH`

The command must write the final video file to `MAGIHUMAN_RESULT_PATH`.

## State Transitions

Implemented:

| From | To | Condition |
| --- | --- | --- |
| `queued` | `running` | worker starts command |
| `running` | `succeeded` | command exits 0 and result file exists |
| `running` | `failed` | command exits non-zero |
| `running` | `failed` | command exits 0 but result file is missing |
| `running` | `failed` | command times out |

Not implemented yet:

- automatic retries
- backoff
- task cancellation while command is running
- stale output cleanup
- multi-worker locking

## Validation

Command:

```powershell
python -m unittest discover -s tests -v
```

Result:

```text
Ran 9 tests in 1.950s
OK
```

Compile check:

```powershell
python -m compileall backend tests
```

Result: passed.

## How It Connects To Real Inference

On a GPU machine, the worker command should be a wrapper that:

1. reads `MAGIHUMAN_PROMPT`, `MAGIHUMAN_MODE`, `MAGIHUMAN_RESOLUTION`, and `MAGIHUMAN_DURATION_SECONDS`
2. calls the proper daVinci-MagiHuman script
3. writes or moves the final mp4 to `MAGIHUMAN_RESULT_PATH`
4. exits non-zero on failure

For the first real integration, use one worker per GPU and one task at a time.

## Next Step

Add cleanup and retry policies after the first GPU inference run reveals real failure modes and output paths.
