# Stage 10: Experiment Matrix

Date: 2026-07-15

Status: complete for test planning and command generation

## Goal

Prepare the concrete test matrix for the GPU host.

This stage converts the todo list into ordered test cases covering:

- first 256p smoke test
- distilled 256p comparison
- 540p super-resolution
- 1080p super-resolution
- multilingual TI2V checks

## Files Added

| File | Purpose |
| --- | --- |
| `backend/experiment_matrix.py` | Builds experiment cases and runner environment variables |
| `tests/test_experiment_matrix.py` | Tests matrix contents and profiles |
| `scripts/generate_experiment_matrix.ps1` | Windows matrix generator |
| `scripts/generate_experiment_matrix.sh` | Linux matrix generator |

## Matrix

| ID | Category | Language | Mode | Resolution | Variant | Required | Depends on |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P01 | performance | en | t2v | 256p | base | yes | - |
| P02 | performance | en | t2v | 256p | distill | no | P01 |
| P03 | performance | en | t2v | 540p | base | yes | P01 |
| P04 | performance | en | t2v | 1080p | base | yes | P01, P03 |
| T01 | multilingual | zh | ti2v | 256p | base | yes | P01 |
| T02 | multilingual | en | ti2v | 256p | base | yes | P01 |
| T03 | multilingual | ja | ti2v | 256p | base | no | P01 |
| T04 | multilingual | ko | ti2v | 256p | base | no | P01 |

## Generate Matrix

```powershell
python -m backend.experiment_matrix --output run_configs/experiment_matrix.json
```

Markdown view:

```powershell
python -m backend.experiment_matrix --format markdown
```

## GPU Execution Pattern

For each case, export the generated `runner_env` values and run:

```bash
bash scripts/magihuman_task_runner.sh
```

Start with `P01`. Do not run `P03`, `P04`, or multilingual cases until `P01` passes and produces valid metrics.

## Validation

Command:

```powershell
python -m unittest discover -s tests -v
```

Result:

```text
Ran 23 tests
OK
```

## Next Step

On a GPU host:

1. Generate `run_configs/experiment_matrix.json`.
2. Run `P01`.
3. Attach metrics JSON to reports.
4. Continue dependent cases only after `P01` passes.
