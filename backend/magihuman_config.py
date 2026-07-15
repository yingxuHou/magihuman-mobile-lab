import argparse
import json
import shlex
from pathlib import Path


PROFILES = {
    ("256p", "base"): {
        "template": "example/base/config.json",
        "checkpoint": "base",
        "br_width": 448,
        "br_height": 256,
        "sr_width": None,
        "sr_height": None,
        "master_port": 6013,
    },
    ("256p", "distill"): {
        "template": "example/distill/config.json",
        "checkpoint": "distill",
        "br_width": 448,
        "br_height": 256,
        "sr_width": None,
        "sr_height": None,
        "master_port": 6015,
    },
    ("540p", "base"): {
        "template": "example/sr_540p/config.json",
        "checkpoint": "base",
        "sr_checkpoint": "540p_sr",
        "br_width": 448,
        "br_height": 256,
        "sr_width": 896,
        "sr_height": 512,
        "master_port": 6017,
    },
    ("1080p", "base"): {
        "template": "example/sr_1080p/config.json",
        "checkpoint": "base",
        "sr_checkpoint": "1080p_sr",
        "br_width": 448,
        "br_height": 256,
        "sr_width": 1920,
        "sr_height": 1088,
        "master_port": 6019,
    },
}


def normalize_variant(resolution, variant):
    if variant == "distill" and resolution != "256p":
        raise ValueError("distill variant is only supported for 256p")
    if variant == "distill":
        return "distill"
    return "base"


def get_profile(resolution, variant="base"):
    variant = normalize_variant(resolution, variant)
    key = (resolution, variant)
    if key not in PROFILES:
        raise ValueError("unsupported resolution/variant: {}/{}".format(resolution, variant))
    profile = dict(PROFILES[key])
    profile["resolution"] = resolution
    profile["variant"] = variant
    return profile


def build_config(repo_dir, model_root, config_dir, resolution, variant="base", cp_size=1):
    repo_dir = Path(repo_dir)
    model_root = Path(model_root)
    config_dir = Path(config_dir)
    profile = get_profile(resolution, variant)

    template_path = repo_dir / profile["template"]
    if not template_path.exists():
        raise FileNotFoundError(str(template_path))

    config = json.loads(template_path.read_text(encoding="utf-8"))
    config["engine_config"]["load"] = str(model_root / "daVinci-MagiHuman" / profile["checkpoint"])
    config["engine_config"]["cp_size"] = int(cp_size)
    config["evaluation_config"]["audio_model_path"] = str(model_root / "stable-audio-open-1.0")
    config["evaluation_config"]["txt_model_path"] = str(model_root / "t5gemma-9b-9b-ul2")
    config["evaluation_config"]["vae_model_path"] = str(model_root / "Wan2.2-TI2V-5B")
    config["evaluation_config"]["student_config_path"] = str(
        model_root / "daVinci-MagiHuman" / "turbo_vae" / "TurboV3-Wan22-TinyShallow_7_7.json"
    )
    config["evaluation_config"]["student_ckpt_path"] = str(
        model_root / "daVinci-MagiHuman" / "turbo_vae" / "checkpoint-340000.ckpt"
    )

    sr_checkpoint = profile.get("sr_checkpoint")
    if sr_checkpoint:
        config["evaluation_config"]["use_sr_model"] = True
        config["evaluation_config"]["sr_model_path"] = str(model_root / "daVinci-MagiHuman" / sr_checkpoint)

    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "{}_{}_config.json".format(resolution, profile["variant"])
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    metadata = dict(profile)
    metadata["config_path"] = str(config_path)
    return metadata


def shell_exports(metadata):
    keys = {
        "MAGIHUMAN_CONFIG_PATH": metadata["config_path"],
        "MAGIHUMAN_BR_WIDTH": metadata["br_width"],
        "MAGIHUMAN_BR_HEIGHT": metadata["br_height"],
        "MAGIHUMAN_SR_WIDTH": metadata.get("sr_width") or "",
        "MAGIHUMAN_SR_HEIGHT": metadata.get("sr_height") or "",
        "MAGIHUMAN_MASTER_PORT": metadata["master_port"],
        "MAGIHUMAN_VARIANT": metadata["variant"],
    }
    return "\n".join("{}={}".format(key, shlex.quote(str(value))) for key, value in keys.items())


def main():
    parser = argparse.ArgumentParser(description="Generate daVinci-MagiHuman run config")
    parser.add_argument("--repo-dir", required=True)
    parser.add_argument("--model-root", required=True)
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--resolution", choices=["256p", "540p", "1080p"], required=True)
    parser.add_argument("--variant", choices=["base", "distill"], default="base")
    parser.add_argument("--cp-size", type=int, default=1)
    parser.add_argument("--format", choices=["json", "shell"], default="json")
    args = parser.parse_args()

    metadata = build_config(
        repo_dir=args.repo_dir,
        model_root=args.model_root,
        config_dir=args.config_dir,
        resolution=args.resolution,
        variant=args.variant,
        cp_size=args.cp_size,
    )

    if args.format == "shell":
        print(shell_exports(metadata))
    else:
        print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()

