# Stage 35: Upstream Drift Audit

Date: 2026-07-16

Status: complete for local tooling and live metadata audit

## Goal

Before spending a GPU session on reproduction, confirm that the project's locked upstream sources still match the current official upstream metadata. If official code or model SHAs move, the project should explicitly decide whether to keep reproducing the locked version or update the lock and repeat static verification.

## What Changed

| File | Purpose |
| --- | --- |
| `backend/upstream_drift_audit.py` | Checks locked GitHub commits and Hugging Face SHAs against current upstream metadata |
| `docs/upstream-drift-audit.json` | Machine-readable live audit result |
| `docs/upstream-drift-audit.md` | Human-readable live audit report |
| `scripts/bootstrap_gpu_host.sh` | Generates upstream drift audit reports during GPU host bootstrap |
| `tests/test_upstream_drift_audit.py` | Covers matching locks, detected drift, unreachable sources, Markdown output, and bootstrap integration |

## Sources Checked

| Source | Locked SHA |
| --- | --- |
| daVinci-MagiHuman GitHub main | `209209b7086eba2020c5439265221495a8357322` |
| MagiCompiler GitHub main | `bfef5bc70226a0c0740e4c551e4f7245a974fb4f` |
| `GAIR/daVinci-MagiHuman` Hugging Face model | `7fe95e50c11bd92bdadf94cd51dbec18427f8e0c` |
| `SII-GAIR/daVinci-MagiHuman` Hugging Face Space | `f4ca1ddf0ab78843686894301a8d0d7ec2cf027b` |

## Live Audit Result

`docs/upstream-drift-audit.md` currently reports:

- Status: `locked_current`
- daVinci-MagiHuman GitHub main: `matches_lock`
- MagiCompiler GitHub main: `matches_lock`
- Hugging Face model: `matches_lock`
- Hugging Face Space: `matches_lock`

This means the existing locked reproduction target is still aligned with the current upstream metadata at the time of this audit.

## GPU Host Usage

Run manually before bootstrap if needed:

```bash
python -m backend.upstream_drift_audit --format markdown
python -m backend.upstream_drift_audit --format json --output outputs/reports/upstream_drift_audit.json
```

The GPU host bootstrap script now writes:

- `outputs/reports/upstream_drift_audit.json`
- `outputs/reports/upstream_drift_audit.md`

Disable only when network metadata access is unavailable:

```bash
UPSTREAM_DRIFT_AUDIT=0 bash scripts/bootstrap_gpu_host.sh
```

Use strict mode when a run must stop if upstream moved or metadata cannot be reached:

```bash
python -m backend.upstream_drift_audit --strict --format markdown
```

## Validation

```powershell
python -m unittest tests.test_upstream_drift_audit -v
python -m backend.upstream_drift_audit --format markdown --output docs/upstream-drift-audit.md
python -m backend.upstream_drift_audit --format json --output docs/upstream-drift-audit.json
```

Result:

- Targeted tests: 5 passed.
- Live metadata audit: `locked_current`.

## Current Limit

This audit does not run inference. It only proves that the project's locked reproduction inputs still match official upstream metadata. Runtime, quality, mobile playback, and cost evidence remain pending until the Linux NVIDIA GPU run completes.
