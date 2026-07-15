# Stage 00: Official Verification

Date: 2026-07-15

Status: complete

## Goal

Verify the project against official sources before running local setup. This stage intentionally avoids relying only on the reposted article.

## Sources Checked

| Source | URL | Result |
| --- | --- | --- |
| Paper | https://arxiv.org/abs/2603.21986 | Available |
| Code | https://github.com/GAIR-NLP/daVinci-MagiHuman | Available |
| Model | https://huggingface.co/GAIR/daVinci-MagiHuman | Available |
| Demo | https://huggingface.co/spaces/SII-GAIR/daVinci-MagiHuman | Available |

## Official Metadata

| Item | Value |
| --- | --- |
| Paper title | Speed by Simplicity: A Single-Stream Architecture for Fast Audio-Video Generative Foundation Model |
| arXiv ID | 2603.21986 |
| arXiv published | 2026-03-23 13:49:06 UTC |
| Code commit checked | `209209b7086eba2020c5439265221495a8357322` |
| HF model sha | `7fe95e50c11bd92bdadf94cd51dbec18427f8e0c` |
| HF model last modified | 2026-03-25 14:00:27 UTC |
| HF Space sha | `f4ca1ddf0ab78843686894301a8d0d7ec2cf027b` |
| HF Space SDK | Gradio |
| License | Apache 2.0 |

## Official Claims To Reproduce

- Architecture: 15B-parameter, 40-layer single-stream Transformer.
- Modalities: text, video, and audio in a unified token sequence.
- Languages: Chinese Mandarin, Cantonese, English, Japanese, Korean, German, French.
- H100 speed for a 5-second video:
  - 256p: 2.0 seconds total.
  - 540p: 8.0 seconds total.
  - 1080p: 38.4 seconds total.
- Evaluation claims:
  - WER: 14.60%.
  - Human preference win rate: 80.0% vs Ovi 1.1 and 60.9% vs LTX 2.3.

## Installation Evidence

The current official README recommends Docker first:

```bash
docker pull sandai/magi-human:latest
docker run -it --gpus all --network host --ipc host \
  -v /path/to/repos:/workspace \
  -v /path/to/checkpoints:/models \
  --name my-magi-human \
  sandai/magi-human:latest \
  bash
```

The README also documents a Conda path:

```bash
conda create -n davinci-magihuman python=3.12
conda activate davinci-magihuman
conda install ffmpeg
pip install torch==2.10.0 torchvision==0.25.0 torchaudio==2.10.0
```

Important discrepancy: the reposted article used `sandai/magi-compiler:latest`, while the current official README uses `sandai/magi-human:latest`. The reproduction should follow the current official README unless Docker pull fails.

## Runtime Entry Points

Official examples found in the GitHub tree:

| Mode | Script |
| --- | --- |
| Base 256p T2V | `example/base/run_T2V.sh` |
| Base 256p TI2V | `example/base/run_TI2V.sh` |
| Distilled 256p T2V | `example/distill/run_T2V.sh` |
| Distilled 256p TI2V | `example/distill/run_TI2V.sh` |
| 540p SR T2V | `example/sr_540p/run_T2V.sh` |
| 540p SR TI2V | `example/sr_540p/run_TI2V.sh` |
| 1080p SR T2V | `example/sr_1080p/run_T2V.sh` |
| 1080p SR TI2V | `example/sr_1080p/run_TI2V.sh` |

The script entry point is:

```text
inference/pipeline/entry.py
```

Base T2V uses:

```bash
torchrun ${DISTRIBUTED_ARGS} inference/pipeline/entry.py \
  --config-load-path example/base/config.json \
  --prompt "$(<example/assets/prompt.txt)" \
  --seconds 4 \
  --br_width 448 \
  --br_height 256 \
  --output_path "output_example_base_t2v_$(date '+%Y%m%d_%H%M%S')"
```

## Required Model Files

Hugging Face API result:

| Item | Value |
| --- | --- |
| File count | 56 |
| Total listed size | 201.27 GiB |
| Largest file | `base/model-00003-of-00007.safetensors` |
| Largest file size | 4.66 GiB |

Top-level model groups:

| Group | Files | Size |
| --- | ---: | ---: |
| `base` | 8 | 28.54 GiB |
| `distill` | 14 | 56.99 GiB |
| `540p_sr` | 14 | 56.99 GiB |
| `1080p_sr` | 14 | 56.99 GiB |
| `turbo_vae` | 2 | 1.74 GiB |

External models required by official config:

| Model | Source |
| --- | --- |
| Text encoder | `google/t5gemma-9b-9b-ul2` |
| Audio model | `stabilityai/stable-audio-open-1.0` |
| VAE | `Wan-AI/Wan2.2-TI2V-5B` |

## Immediate Impact On Mobile Feasibility

This stage does not prove runtime feasibility yet, because no local or cloud inference has been executed.

It does provide strong package-size evidence:

- The official model stack is about 201.27 GiB before counting external models.
- The base checkpoint group alone is about 28.54 GiB.
- That size is already not suitable for bundling inside a normal mobile app package.

The next required evidence is local hardware capability and actual inference memory/latency.

## Next Step

Run Stage 01 environment inspection:

```powershell
nvidia-smi
nvcc --version
git --version
git lfs version
conda --version
docker --version
ffmpeg -version
python --version
```
