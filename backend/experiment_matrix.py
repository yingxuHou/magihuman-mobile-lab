import argparse
import json
from pathlib import Path

from backend.magihuman_config import get_profile


def default_cases():
    return [
        {
            "id": "P01",
            "name": "base_256p_t2v_smoke",
            "category": "performance",
            "language": "en",
            "mode": "t2v",
            "resolution": "256p",
            "variant": "base",
            "duration_seconds": 5,
            "seed": 42,
            "prompt": "A professional presenter looks at the camera and says hello to the audience in a calm voice.",
            "depends_on": [],
            "required": True,
        },
        {
            "id": "P02",
            "name": "distill_256p_t2v",
            "category": "performance",
            "language": "en",
            "mode": "t2v",
            "resolution": "256p",
            "variant": "distill",
            "duration_seconds": 5,
            "seed": 42,
            "prompt": "A professional presenter briefly introduces a new AI video generation demo.",
            "depends_on": ["P01"],
            "required": False,
        },
        {
            "id": "P03",
            "name": "sr_540p_t2v",
            "category": "performance",
            "language": "en",
            "mode": "t2v",
            "resolution": "540p",
            "variant": "base",
            "duration_seconds": 5,
            "seed": 42,
            "prompt": "A professional presenter explains the cloud inference result in one short sentence.",
            "depends_on": ["P01"],
            "required": True,
        },
        {
            "id": "P04",
            "name": "sr_1080p_t2v",
            "category": "performance",
            "language": "en",
            "mode": "t2v",
            "resolution": "1080p",
            "variant": "base",
            "duration_seconds": 5,
            "seed": 42,
            "prompt": "A professional presenter summarizes the mobile app feasibility test.",
            "depends_on": ["P01", "P03"],
            "required": True,
        },
        {
            "id": "T01",
            "name": "mandarin_ti2v",
            "category": "multilingual",
            "language": "zh",
            "mode": "ti2v",
            "resolution": "256p",
            "variant": "base",
            "duration_seconds": 5,
            "seed": 42,
            "prompt": "一个穿着白衬衫的主持人看着镜头，用普通话说：大家好，欢迎观看这个数字人演示。",
            "depends_on": ["P01"],
            "required": True,
        },
        {
            "id": "T02",
            "name": "english_ti2v",
            "category": "multilingual",
            "language": "en",
            "mode": "ti2v",
            "resolution": "256p",
            "variant": "base",
            "duration_seconds": 5,
            "seed": 42,
            "prompt": "A presenter looks at the camera and says: Hello, this is a mobile app cloud rendering test.",
            "depends_on": ["P01"],
            "required": True,
        },
        {
            "id": "T03",
            "name": "japanese_ti2v",
            "category": "multilingual",
            "language": "ja",
            "mode": "ti2v",
            "resolution": "256p",
            "variant": "base",
            "duration_seconds": 5,
            "seed": 42,
            "prompt": "司会者がカメラを見て、日本語で「こんにちは、これはデジタルヒューマンのテストです」と話します。",
            "depends_on": ["P01"],
            "required": False,
        },
        {
            "id": "T04",
            "name": "korean_ti2v",
            "category": "multilingual",
            "language": "ko",
            "mode": "ti2v",
            "resolution": "256p",
            "variant": "base",
            "duration_seconds": 5,
            "seed": 42,
            "prompt": "진행자가 카메라를 바라보며 한국어로 말합니다. 안녕하세요, 이것은 디지털 휴먼 테스트입니다.",
            "depends_on": ["P01"],
            "required": False,
        },
    ]


def build_case_command(case, result_dir="outputs/experiment-results"):
    result_path = "{}/{}.mp4".format(result_dir.rstrip("/"), case["id"])
    env = {
        "MAGIHUMAN_TASK_ID": case["id"],
        "MAGIHUMAN_PROMPT": case["prompt"],
        "MAGIHUMAN_MODE": case["mode"],
        "MAGIHUMAN_RESOLUTION": case["resolution"],
        "MAGIHUMAN_DURATION_SECONDS": str(case["duration_seconds"]),
        "MAGIHUMAN_SEED": str(case["seed"]),
        "MAGIHUMAN_MODEL_VARIANT": case["variant"],
        "MAGIHUMAN_RESULT_PATH": result_path,
    }
    if case["mode"] == "ti2v":
        env["MAGIHUMAN_IMAGE_PATH"] = "third_party/daVinci-MagiHuman/example/assets/image.png"
    return env


def build_matrix():
    matrix = []
    for case in default_cases():
        profile = get_profile(case["resolution"], case["variant"])
        item = dict(case)
        item["profile"] = {
            "br_width": profile["br_width"],
            "br_height": profile["br_height"],
            "sr_width": profile.get("sr_width"),
            "sr_height": profile.get("sr_height"),
            "config_template": profile["template"],
        }
        item["runner_env"] = build_case_command(case)
        matrix.append(item)
    return matrix


def write_matrix(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    matrix = build_matrix()
    path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8")
    return matrix


def markdown_table(matrix):
    lines = [
        "| ID | Category | Language | Mode | Resolution | Variant | Required | Depends on |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case in matrix:
        lines.append(
            "| {id} | {category} | {language} | {mode} | {resolution} | {variant} | {required} | {depends} |".format(
                id=case["id"],
                category=case["category"],
                language=case["language"],
                mode=case["mode"],
                resolution=case["resolution"],
                variant=case["variant"],
                required="yes" if case["required"] else "no",
                depends=", ".join(case["depends_on"]) if case["depends_on"] else "-",
            )
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate MagiHuman experiment matrix")
    parser.add_argument("--output", default="run_configs/experiment_matrix.json")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    args = parser.parse_args()

    matrix = write_matrix(args.output)
    if args.format == "markdown":
        print(markdown_table(matrix))
    else:
        print(json.dumps(matrix, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
