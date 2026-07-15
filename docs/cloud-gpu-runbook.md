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
nvidia-smi
docker --version
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
git --version
git lfs version
python3 --version
df -h
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

Summarize results:

```bash
python -m backend.experiment_results --log-dir logs --format markdown
```
