# Cloud GPU Runbook

This runbook is for the machine that will actually run daVinci-MagiHuman inference.

## Target Machine

Preferred:

- Linux
- NVIDIA H100
- Docker
- NVIDIA Container Toolkit
- At least 500 GiB disk

Minimum for exploratory testing:

- High-VRAM NVIDIA GPU
- Working `nvidia-smi`
- Enough disk for the selected checkpoint group and external models

## 1. Clone Project

```bash
git clone https://github.com/yingxuHou/magihuman-mobile-lab.git
cd magihuman-mobile-lab
```

## 2. Preferred Bootstrap Workflow

Use the bootstrap script on a fresh GPU host. It runs host preflight, writes the bootstrap plan, creates `outputs/run_magi_container.sh`, and can pull the official Docker image.

```bash
export HF_TOKEN="<your_huggingface_token>"
bash scripts/bootstrap_gpu_host.sh
bash outputs/run_magi_container.sh
```

The bootstrap script also writes `outputs/reports/upstream_drift_audit.md` and `.json` by default. Confirm the status is `locked_current` before spending GPU time. If the GPU host cannot reach GitHub/Hugging Face metadata, run:

```bash
python -m backend.upstream_drift_audit --format markdown
```

Use `UPSTREAM_DRIFT_AUDIT=0 bash scripts/bootstrap_gpu_host.sh` only when metadata access is unavailable and the locked commits were already checked elsewhere.

Inside the container:

```bash
INSTALL_MAGICOMPILER=1 bash scripts/run_gpu_reproduction_workflow.sh
```

The workflow runs upstream audit, locked source preparation, P01, P01 acceptance, full required suite, required-suite acceptance, and evidence packaging. It stops on the first failed gate.

The workflow starts with a static readiness audit. You can run it manually before entering a long GPU session:

```bash
python -m backend.workflow_readiness_audit --format markdown --strict
```

The bootstrap path locks source repositories to the verified commits:

- daVinci-MagiHuman: `209209b7086eba2020c5439265221495a8357322`
- MagiCompiler: `bfef5bc70226a0c0740e4c551e4f7245a974fb4f`

The generated Docker command passes `HF_TOKEN` and `HUGGINGFACE_HUB_TOKEN` into the container, so set one of them on the host before running `outputs/run_magi_container.sh`.

The manual steps below are retained for debugging individual setup failures.

## 3. Check Environment

```bash
bash scripts/cloud_env_check.sh
python -m backend.gpu_preflight --mode host --format markdown
```

## 4. Pull Official Docker Image

```bash
docker pull sandai/magi-human:latest
```

## 5. Start Container

```bash
mkdir -p third_party models outputs logs

docker run -it --gpus all --network host --ipc host \
  -v "$PWD/third_party:/workspace" \
  -v "$PWD/models:/models" \
  -v "$PWD/outputs:/outputs" \
  -v "$PWD/logs:/logs" \
  --name my-magi-human \
  sandai/magi-human:latest \
  bash
```

## 6. Inside Container

```bash
cd /workspace
git clone https://github.com/SandAI-org/MagiCompiler.git
cd MagiCompiler
pip install -r requirements.txt
pip install .
cd /workspace
git clone https://github.com/GAIR-NLP/daVinci-MagiHuman
cd daVinci-MagiHuman
```

## 7. Download Checkpoints

The official README requires:

- `GAIR/daVinci-MagiHuman`
- `google/t5gemma-9b-9b-ul2`
- `stabilityai/stable-audio-open-1.0`
- `Wan-AI/Wan2.2-TI2V-5B`

Use `huggingface-cli download` after confirming access and disk capacity.

For the first P01 smoke run, download only the P01 profile:

```bash
MODEL_PROFILE=p01 bash scripts/download_models.sh
```

The download script logs every Hugging Face command as `download_command=...`. After a pipeline download, audit the log before trusting the checkpoint footprint:

```bash
python -m backend.download_log_audit --profile p01 --log logs/p01_download_models_<timestamp>.log --format markdown
python -m backend.download_log_audit --profile required_suite --log logs/download_models_<timestamp>.log --format markdown
```

The P01 and full GPU pipelines run the matching audit automatically when `DOWNLOAD_MODELS=1`.

For the final required suite, download:

```bash
MODEL_PROFILE=required_suite bash scripts/download_models.sh
```

For a full mirror including distill:

```bash
MODEL_PROFILE=complete bash scripts/download_models.sh
```

The pipeline checks Hugging Face auth before download when `DOWNLOAD_MODELS=1`. Either set `HF_TOKEN`/`HUGGINGFACE_HUB_TOKEN` or run `huggingface-cli login` inside the container.

Before downloading, verify repository and gated-file access with lightweight HEAD probes:

```bash
python -m backend.hf_access_audit --profile p01 --format markdown
python -m backend.hf_access_audit --profile required_suite --format markdown
```

The P01 and full GPU pipelines run this access audit automatically before `scripts/download_models.sh` when `DOWNLOAD_MODELS=1`. P01 writes `logs/p01_hf_access_<timestamp>.json` and `outputs/reports/p01_hf_access_<timestamp>.md`; the full pipeline writes `logs/hf_access_<timestamp>.json` and `outputs/reports/hf_access_<timestamp>.md`.

After download, audit checkpoint footprints:

```bash
python -m backend.model_audit --model-root models --profile p01 --format markdown
python -m backend.model_audit --model-root models --profile required_suite --format markdown
```

The P01 and full GPU pipelines run a report-only audit before download, then run a strict audit after download. If `EXECUTE=1` is used without `DOWNLOAD_MODELS=1`, the initial model audit is strict because models are expected to already exist.

At the end of a successful pipeline, check the artifact audit report before packaging evidence:

```bash
python -m backend.pipeline_artifact_audit --run p01 --stamp "<timestamp>" --download-models --execute --format markdown
python -m backend.pipeline_artifact_audit --run full --stamp "<timestamp>" --download-models --execute --format markdown
```

The P01 pipeline writes `outputs/reports/p01_pipeline_artifact_audit_<timestamp>.md`; the full pipeline writes `outputs/reports/pipeline_artifact_audit_<timestamp>.md`. These reports confirm whether expected logs, reports, metrics JSON, and result MP4 files exist.

## 8. First Smoke Test

Start with the worker-compatible runner:

```bash
INSTALL_MAGICOMPILER=1 DOWNLOAD_MODELS=1 EXECUTE=1 bash scripts/run_p01_smoke_pipeline.sh
```

This runs only P01: 256p, T2V, base model, 5 seconds. Continue to the full suite only after P01 writes a playable mp4, metrics JSON, matching run context, and an acceptance report whose status starts with `ready_for_full_suite`.

Before download or execution, the P01 pipeline checks that `docs/p01-smoke-manifest.json` matches the generated P01 plan. It writes:

- `logs/p01_smoke_plan_audit_<timestamp>.json`
- `outputs/reports/p01_smoke_plan_audit_<timestamp>.md`

Manual check:

```bash
python -m backend.smoke_plan_audit --format markdown
```

Manual comparison commands:

```bash
cd /workspace/daVinci-MagiHuman
bash example/base/run_T2V.sh
```

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

The raw official script is still useful for comparison:

```bash
cd third_party/daVinci-MagiHuman
bash example/base/run_T2V.sh
```

Record:

- Command
- GPU model
- Peak VRAM
- Total runtime
- Output path
- Log path
- Whether mp4 plays correctly
- Metrics JSON path from `scripts/magihuman_task_runner.sh`
- Mobile video compatibility report from `python -m backend.mobile_video_check --log-dir logs --cases P01 --format markdown`
- P01 acceptance report from `python -m backend.p01_acceptance --log-dir logs --result-path outputs/smoke-test/P01.mp4 --format markdown`
- P01 checkpoint audit report from `python -m backend.model_audit --model-root models --profile p01 --format markdown`

The P01 pipeline writes:

- `logs/p01_acceptance_<timestamp>.json`
- `outputs/reports/p01_acceptance_<timestamp>.md`

If the status is `not_ready`, do not run P03/P04/T01/T02 yet. If the status is `ready_for_full_suite_with_transcode_required`, the full suite may run, but final mobile feasibility must include a mobile delivery transcode path.

If metrics are not generated automatically, run:

```bash
python -m backend.run_metrics \
  --log <log_path> \
  --smi-csv <nvidia_smi_log> \
  --video <result_path> \
  --output <metrics_json>
```

## 9. Report Back

After each run, update:

- `docs/reproduction-log.md`
- `docs/mobile-feasibility.md`
- a stage report under `docs/`

Then commit and push:

```bash
git status
git add docs scripts 7.15-todolist.md
git commit -m "Record <stage>"
git push
```

## 10. Experiment Matrix

Generate the ordered test plan:

```bash
python -m backend.experiment_matrix --output run_configs/experiment_matrix.json
python -m backend.experiment_matrix --format markdown
```

Run `P01` first. Continue with `P03`, `P04`, and multilingual TI2V cases only after `P01` produces a playable mp4, valid metrics JSON, and a passing P01 acceptance report.

Dry-run a case:

```bash
bash scripts/run_experiment_case.sh P01
```

Execute a case:

```bash
bash scripts/run_experiment_case.sh P01 --execute
```

Summarize results:

```bash
python -m backend.experiment_results --log-dir logs --format markdown
python -m backend.mobile_video_check --log-dir logs --format markdown
```

## 11. Pipeline Workflow

After the host is prepared, prefer the pipeline script so preflight, runs, summaries, and the feasibility decision are generated together.

End-to-end workflow inside the container:

```bash
INSTALL_MAGICOMPILER=1 bash scripts/run_gpu_reproduction_workflow.sh
```

This is the preferred path for a real reproduction attempt because it runs P01 before the full suite and packages evidence after the gates pass.
It writes `logs/gpu_workflow_readiness_<timestamp>.json` and `outputs/reports/gpu_workflow_readiness_<timestamp>.md` before any model download or inference.

Dry run:

```bash
bash scripts/gpu_reproduction_pipeline.sh
```

Download models and execute required cases:

```bash
INSTALL_MAGICOMPILER=1 DOWNLOAD_MODELS=1 EXECUTE=1 bash scripts/gpu_reproduction_pipeline.sh
```

Run inside a prepared container without downloading models:

```bash
EXECUTE=1 bash scripts/gpu_reproduction_pipeline.sh
```

The pipeline writes timestamped reports under `outputs/reports/` and logs under `logs/`.

It also writes a mobile video compatibility report. If the report returns `mobile_video_needs_transcode`, use the printed `ffmpeg` command as the starting point for a mobile delivery copy.

When `EXECUTE=1`, the full pipeline also writes:

- `logs/required_suite_acceptance_<timestamp>.json`
- `outputs/reports/required_suite_acceptance_<timestamp>.md`

Only start quality review and cost review after the required-suite acceptance status starts with `ready_for_quality_and_cost_review`. If the status is `ready_for_quality_and_cost_review_with_transcode_required`, continue review but keep mobile transcoding as a required product task.

## 12. Quality Review

After generated videos exist, create and fill a review file:

```bash
python -m backend.required_suite_acceptance --log-dir logs --result-dir outputs/experiment-results --p01-result-path outputs/smoke-test/P01.mp4 --format markdown
python -m backend.quality_review --create-template --output docs/quality-review.json
python -m backend.quality_review --review docs/quality-review.json --format markdown
```

Then rerun the final decision with the review file:

```bash
python -m backend.feasibility_decision --log-dir logs --quality-review docs/quality-review.json --format markdown
```

Or pass the review file to the pipeline:

```bash
QUALITY_REVIEW=docs/quality-review.json EXECUTE=1 bash scripts/gpu_reproduction_pipeline.sh
```

## 13. Cost Review

After metrics exist, create and fill a cost review:

```bash
python -m backend.cost_review --create-template --output docs/cost-review.json
python -m backend.cost_review --review docs/cost-review.json --log-dir logs --format markdown
```

Then rerun the final decision with both review files:

```bash
python -m backend.feasibility_decision \
  --log-dir logs \
  --quality-review docs/quality-review.json \
  --cost-review docs/cost-review.json \
  --format markdown
```

## 14. Final Report

Generate the combined report after runtime, quality, and cost evidence are available:

```bash
python -m backend.final_report \
  --log-dir logs \
  --quality-review docs/quality-review.json \
  --cost-review docs/cost-review.json \
  --format markdown \
  --output docs/mobile-feasibility-report.md
```

The pipeline also writes a timestamped report under `outputs/reports/`.

## 15. Package Evidence For Import

Package only small evidence files. Do not include model weights or generated videos.

```bash
bash scripts/package_gpu_evidence.sh
```

The evidence package includes metrics, preflight JSON, model audit JSON, report files, the P01 smoke manifest, `evidence-provenance.json` / `evidence-provenance.md`, and an `evidence-manifest.json` / `evidence-manifest.md`. The manifest rejects video files and model weights.

Before importing the package, inspect `evidence-provenance.md`. It should show the project commit used on the GPU host, the locked daVinci-MagiHuman and MagiCompiler commits, and the P01 manifest hash.

Copy the produced archive back to the local repository machine, unpack it into the project root, then audit:

```bash
bash scripts/import_gpu_evidence_package.sh outputs/gpu-evidence-<timestamp>.tar.gz
```

On Windows:

```powershell
.\scripts\import_gpu_evidence_package.ps1 -Archive outputs\gpu-evidence-<timestamp>.tar.gz
```
