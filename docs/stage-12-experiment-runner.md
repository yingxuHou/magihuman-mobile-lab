# Stage 12: Experiment Runner

Date: 2026-07-15

Status: complete for local planning and dependency checks

## Goal

Add a case-level execution tool for the GPU host.

Before this stage, the project could generate a matrix and summarize metrics, but running a specific case still required manually copying environment variables. This stage adds a runner that can:

- find a case by id
- check whether dependency cases already have measured metrics
- print shell exports for dry-run review
- execute `scripts/magihuman_task_runner.sh` on the GPU host

## Files Added

| File | Purpose |
| --- | --- |
| `backend/experiment_runner.py` | Case runner and dependency checker |
| `tests/test_experiment_runner.py` | Unit tests for case selection, dependency status, and dry-run command output |
| `scripts/run_experiment_case.ps1` | Windows launcher |
| `scripts/run_experiment_case.sh` | Linux launcher |

## Usage

Dry run:

```powershell
python -m backend.experiment_runner --case P01
```

Linux wrapper:

```bash
bash scripts/run_experiment_case.sh P01
```

Execute on GPU host:

```bash
bash scripts/run_experiment_case.sh P01 --execute
```

Run a dependent case only after dependencies are measured:

```bash
bash scripts/run_experiment_case.sh P04 --execute
```

If dependencies are intentionally bypassed:

```bash
bash scripts/run_experiment_case.sh P04 --execute --force
```

## Dependency Rules

- `P01` has no dependency.
- `P03` depends on `P01`.
- `P04` depends on `P01` and `P03`.
- `T01` to `T04` depend on `P01`.

The runner checks metrics under `logs/`. A dependency counts as satisfied only when the corresponding case has a `measured` metrics summary.

## Validation

Command:

```powershell
python -m unittest discover -s tests -v
```

Result:

```text
Ran 32 tests
OK
```

## Next Step

On the GPU host:

1. Run `bash scripts/run_experiment_case.sh P01 --execute`.
2. Summarize with `python -m backend.experiment_results --log-dir logs --format markdown`.
3. Commit and push the updated report.
4. Continue with `P03`, `P04`, `T01`, and `T02` after dependencies pass.
