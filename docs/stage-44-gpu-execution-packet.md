# Stage 44 GPU Execution Packet

## Purpose

Stage 44 creates a single handoff packet for the Linux NVIDIA GPU operator. The packet does not run inference locally. It gathers the repository URL, branch, Docker image, P01 manifest hash, workflow readiness status, GPU host commands, expected evidence artifacts, and local import commands.

The goal is to make the first real GPU run less dependent on manually reading multiple runbooks.

## Generated Artifacts

- `docs/gpu-execution-packet.md`
- `docs/gpu-execution-packet.json`

Packet status:

- Original Stage 44 status: `ready_for_gpu_handoff`
- Current status after Stage 50: `ready_for_gpu_handoff` with the P01 budget guard ready
- Local runtime status: `not_executed_on_this_workstation`
- Repository: `https://github.com/yingxuHou/magihuman-mobile-lab.git`
- Docker image: `sandai/magi-human:latest`

## Commands

Generate the packet:

```powershell
python -m backend.gpu_execution_packet --format markdown --output docs/gpu-execution-packet.md
python -m backend.gpu_execution_packet --format json --output docs/gpu-execution-packet.json
```

Wrapper scripts:

```bash
bash scripts/generate_gpu_execution_packet.sh --format markdown --output docs/gpu-execution-packet.md
```

```powershell
.\scripts\generate_gpu_execution_packet.ps1 --format markdown --output docs/gpu-execution-packet.md
```

## GPU Host Handoff

The packet tells the GPU operator to clone this repository, set `HF_TOKEN`, run `scripts/bootstrap_gpu_host.sh`, enter the generated container, run `scripts/run_gpu_reproduction_workflow.sh`, then return `outputs/gpu-evidence-*.tar.gz` for local import.

The final mobile App recommendation must not change until imported runtime evidence, quality review, cost review, and final report gates pass.

## Validation

Targeted validation passed:

```powershell
python -m unittest tests.test_gpu_execution_packet -v
```

The full local suite should pass 180 tests.
