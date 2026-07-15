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

## 2. Check Environment

```bash
bash scripts/cloud_env_check.sh
python -m backend.gpu_preflight --mode host --format markdown
```

## 3. Pull Official Docker Image

```bash
docker pull sandai/magi-human:latest
```

## 4. Start Container

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

## 5. Inside Container

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

## 6. Download Checkpoints

The official README requires:

- `GAIR/daVinci-MagiHuman`
- `google/t5gemma-9b-9b-ul2`
- `stabilityai/stable-audio-open-1.0`
- `Wan-AI/Wan2.2-TI2V-5B`

Use `huggingface-cli download` after confirming access and disk capacity.

## 7. First Smoke Test

Start with the worker-compatible runner:

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

If metrics are not generated automatically, run:

```bash
python -m backend.run_metrics \
  --log <log_path> \
  --smi-csv <nvidia_smi_log> \
  --video <result_path> \
  --output <metrics_json>
```

## 8. Report Back

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

## 9. Experiment Matrix

Generate the ordered test plan:

```bash
python -m backend.experiment_matrix --output run_configs/experiment_matrix.json
python -m backend.experiment_matrix --format markdown
```

Run `P01` first. Continue with `P03`, `P04`, and multilingual TI2V cases only after `P01` produces a playable mp4 and valid metrics JSON.

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
```

## 10. Pipeline Workflow

After the host is prepared, prefer the pipeline script so preflight, runs, summaries, and the feasibility decision are generated together.

Dry run:

```bash
bash scripts/gpu_reproduction_pipeline.sh
```

Download models and execute required cases:

```bash
DOWNLOAD_MODELS=1 EXECUTE=1 bash scripts/gpu_reproduction_pipeline.sh
```

Run inside a prepared container without downloading models:

```bash
EXECUTE=1 bash scripts/gpu_reproduction_pipeline.sh
```

The pipeline writes timestamped reports under `outputs/reports/` and logs under `logs/`.

## 11. Quality Review

After generated videos exist, create and fill a review file:

```bash
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

## 12. Cost Review

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

## 13. Final Report

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

## 14. Package Evidence For Import

Package only small evidence files. Do not include model weights or generated videos.

```bash
bash scripts/package_gpu_evidence.sh
```

Copy the produced archive back to the local repository machine, unpack it into the project root, then audit:

```bash
python -m backend.evidence_import \
  --log-dir logs \
  --quality-review docs/quality-review.json \
  --cost-review docs/cost-review.json \
  --final-report-output docs/mobile-feasibility-report.md \
  --format markdown \
  --output docs/gpu-evidence-import-audit.md
```
