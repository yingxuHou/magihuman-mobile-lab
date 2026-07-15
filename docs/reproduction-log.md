# Reproduction Log

This file records environment checks, setup commands, inference runs, failures, and measured results.

## 2026-07-15

- Created project plan for reproducing daVinci-MagiHuman.
- Added measurement-first criteria for deciding mobile app feasibility.
- Completed Stage 00 official verification.
- Confirmed current official Docker image is `sandai/magi-human:latest`; the reposted article mentions `sandai/magi-compiler:latest`, so the official README takes priority.
- Recorded code commit `209209b7086eba2020c5439265221495a8357322`.
- Recorded Hugging Face model sha `7fe95e50c11bd92bdadf94cd51dbec18427f8e0c`.
- Recorded model stack size from Hugging Face API: about 201.27 GiB across 56 files.
- Identified base smoke-test script: `example/base/run_T2V.sh`.
- Completed Stage 01 local environment check.
- Local machine has Intel Iris Xe Graphics only; no NVIDIA GPU was detected.
- `nvidia-smi`, `nvcc`, Docker, Conda, and torch are unavailable in the current environment.
- Local full inference reproduction is not viable on this machine. Continue local source/runbook preparation and move actual inference to a cloud or remote NVIDIA GPU environment.
- No inference run has been completed yet.
