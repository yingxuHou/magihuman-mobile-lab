import json
import tempfile
import unittest
from pathlib import Path

from backend.smoke_manifest import build_p01_manifest, markdown_report


class SmokeManifestTest(unittest.TestCase):
    def create_repo(self, root):
        repo = root / "third_party" / "daVinci-MagiHuman"
        (repo / "example" / "assets").mkdir(parents=True)
        (repo / "example" / "base").mkdir(parents=True)
        (repo / "example" / "assets" / "prompt.txt").write_text("official prompt text", encoding="utf-8")
        (repo / "example" / "assets" / "image.png").write_bytes(b"fake image bytes")
        (repo / "example" / "base" / "config.json").write_text(
            json.dumps(
                {
                    "engine_config": {"load": "/old", "cp_size": 1},
                    "evaluation_config": {
                        "num_inference_steps": 32,
                        "use_turbo_vae": True,
                    },
                }
            ),
            encoding="utf-8",
        )
        (repo / "example" / "base" / "run_T2V.sh").write_text(
            "torchrun inference/pipeline/entry.py --seconds 4 --br_width 448 --br_height 256\n",
            encoding="utf-8",
        )
        return repo

    def test_build_p01_manifest_records_actual_inputs_and_official_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_repo(root)
            manifest = build_p01_manifest(project_root=root)

        actual = manifest["actual_p01_inputs"]
        official = manifest["official_example"]

        self.assertEqual(manifest["status"], "ready_for_gpu_execution")
        self.assertEqual(actual["case_id"], "P01")
        self.assertEqual(actual["duration_seconds"], 5)
        self.assertEqual(actual["seed"], 42)
        self.assertEqual(actual["expected_result_path"], "outputs/smoke-test/P01.mp4")
        self.assertEqual(actual["runner_env"]["MAGIHUMAN_MANIFEST_PATH"], "docs/p01-smoke-manifest.json")
        self.assertFalse(actual["reference_image_required"])
        self.assertEqual(official["base_t2v_script"]["seconds"], 4)
        self.assertEqual(official["base_t2v_script"]["br_width"], 448)
        self.assertFalse(official["base_t2v_script"]["passes_seed_argument"])
        self.assertEqual(official["base_config"]["engine_seed_default"], 1234)
        self.assertTrue(official["reference_image"]["used_by_ti2v_cases"])

    def test_markdown_report_contains_reproduction_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_repo(root)
            report = markdown_report(build_p01_manifest(project_root=root))

        self.assertIn("P01 Smoke Input Manifest", report)
        self.assertIn("outputs/smoke-test/P01.mp4", report)
        self.assertIn("| Seed | 42 |", report)
        self.assertIn("| Official script seconds | 4 |", report)


if __name__ == "__main__":
    unittest.main()
