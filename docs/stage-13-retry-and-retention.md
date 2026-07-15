# Stage 13: Retry And Retention Policies

Date: 2026-07-16

Status: complete for local prototype

## Goal

Close two backend gaps from the todo list:

- automatic failure retry
- generated video expiration cleanup

These are required for a practical mobile app backed by GPU inference. Users need retries for transient GPU failures, and generated media cannot be retained forever without a cleanup policy.

## Files Changed

| File | Purpose |
| --- | --- |
| `backend/task_store.py` | Adds retry and result timestamp fields |
| `backend/worker.py` | Requeues failed tasks when retries remain |
| `backend/retention.py` | Deletes expired result files and records expiration |
| `tests/test_worker.py` | Tests retry behavior |
| `tests/test_retention.py` | Tests result cleanup behavior |
| `scripts/cleanup_results.ps1` | Windows cleanup launcher |
| `scripts/cleanup_results.sh` | Linux cleanup launcher |

## Retry Behavior

New task fields:

- `retry_count`
- `max_retries`

Failure cases that can trigger retry:

- worker timeout
- command exits non-zero
- command exits successfully but does not create result file

If `retry_count < max_retries`, the task returns to `queued` with `worker.status = retry_queued`.

If retries are exhausted, the task becomes `failed`.

## Retention Behavior

New task fields:

- `result_created_at`
- `result_expired_at`

Cleanup command:

```powershell
python -m backend.retention --data-dir api_data --ttl-seconds 86400
```

For each expired result:

- result file is deleted if present
- `result_path` is cleared
- `result_expired_at` is recorded

## Validation

Command:

```powershell
python -m unittest discover -s tests -v
```

Result:

```text
Ran 35 tests
OK
```

## Next Step

After the first GPU run, set a realistic retention window based on storage cost and user workflow. A starting value for demos is 24 hours; production may need user-configurable retention.
