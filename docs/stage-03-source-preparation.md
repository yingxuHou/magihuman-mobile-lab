# Stage 03: Source Preparation

Date: 2026-07-15

Status: complete for local source preparation

## Goal

Clone and inspect the official source repositories without committing third-party code into this project repository.

## Repositories Cloned Locally

Both repositories were cloned under ignored `third_party/` paths.

| Repository | Local path | Commit |
| --- | --- | --- |
| `GAIR-NLP/daVinci-MagiHuman` | `third_party/daVinci-MagiHuman` | `209209b7086eba2020c5439265221495a8357322` |
| `SandAI-org/MagiCompiler` | `third_party/MagiCompiler` | `bfef5bc70226a0c0740e4c551e4f7245a974fb4f` |

`third_party/` remains ignored by Git, so external source is not pushed into this repo.

## daVinci-MagiHuman Structure

Important paths:

| Path | Purpose |
| --- | --- |
| `README.md` | Official setup and usage |
| `requirements.txt` | Main Python dependencies |
| `requirements-nodeps.txt` | `openai-whisper`, `tiktoken` |
| `example/assets/prompt.txt` | Official sample prompt |
| `example/assets/image.png` | Official sample reference image |
| `example/base/config.json` | Base 256p config |
| `example/distill/config.json` | Distilled config |
| `example/sr_540p/config.json` | 540p SR config |
| `example/sr_1080p/config.json` | 1080p SR config |
| `inference/pipeline/entry.py` | CLI inference entry point |

## Runtime Behavior Found In Source

`inference/pipeline/entry.py`:

- Requires `--prompt`.
- Requires `--save_path_prefix` or `--output_path`.
- Uses `--image_path` to switch from T2V to TI2V mode.
- Accepts optional runtime controls:
  - `--seed`
  - `--seconds`
  - `--br_width`
  - `--br_height`
  - `--sr_width`
  - `--sr_height`
  - `--output_width`
  - `--output_height`
  - `--upsample_mode`

The config loader accepts:

```bash
--config-load-path example/base/config.json
```

## Config Path Requirements

Base config requires these local paths:

| Config key | Required target |
| --- | --- |
| `engine_config.load` | daVinci-MagiHuman base checkpoint |
| `evaluation_config.audio_model_path` | `stable-audio-open-1.0` |
| `evaluation_config.txt_model_path` | `t5gemma-9b-9b-ul2` |
| `evaluation_config.vae_model_path` | `Wan2.2-TI2V-5B` |
| `evaluation_config.student_config_path` | Turbo VAE JSON |
| `evaluation_config.student_ckpt_path` | Turbo VAE checkpoint |

Distill config changes:

- `engine_config.load` points to `distill`.
- `engine_config.distill` is `true`.
- `evaluation_config.cfg_number` is `1`.
- `evaluation_config.num_inference_steps` is `8`.

1080p SR config adds:

- `evaluation_config.use_sr_model` is `true`.
- `evaluation_config.sr_model_path` points to `1080p_sr`.
- `evaluation_config.sr_num_inference_steps` is `5`.
- `evaluation_config.sr_cfg_number` is `1`.

## Scripts Added

| Script | Purpose |
| --- | --- |
| `scripts/cloud_env_check.sh` | Linux GPU environment checks |
| `scripts/download_models.sh` | Hugging Face model downloads |
| `scripts/run_base_t2v_smoke.sh` | Base 256p T2V smoke test wrapper with log and `nvidia-smi` capture |

## Current Limitation

No inference was run in this stage because the current workstation lacks NVIDIA GPU/CUDA/Docker/Conda.

Shell script syntax was not validated locally because `bash` resolves to the Windows/WSL launcher on this machine and `bash -n` timed out. These scripts should be validated on the target Linux GPU host before model download or inference.

## Next Step

Use the cloud GPU runbook and scripts on a suitable GPU machine. The first actual inference target remains base 256p T2V.
