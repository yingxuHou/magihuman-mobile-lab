import tempfile
import unittest
from pathlib import Path

from backend.gpu_preflight import build_preflight, command_check, markdown_preflight, path_check


def fake_lookup(command):
    return "/usr/bin/{}".format(command)


class GpuPreflightTest(unittest.TestCase):
    def test_command_check_uses_lookup(self):
        check = command_check("torchrun", "torchrun", lookup=fake_lookup)

        self.assertTrue(check["ok"])
        self.assertEqual(check["detail"], "/usr/bin/torchrun")

    def test_path_check_missing_required(self):
        check = path_check("missing", "does-not-exist", required=True)

        self.assertFalse(check["ok"])
        self.assertTrue(check["required"])

    def test_ready_when_required_paths_and_commands_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "third_party" / "daVinci-MagiHuman"
            model_root = root / "models"
            repo.mkdir(parents=True)
            for model_dir in ["daVinci-MagiHuman", "t5gemma-9b-9b-ul2", "stable-audio-open-1.0", "Wan2.2-TI2V-5B"]:
                (model_root / model_dir).mkdir(parents=True)

            report = build_preflight(
                project_root=root,
                repo_dir=repo,
                model_root=model_root,
                mode="container",
                require_models=True,
                min_disk_gib=0,
                command_lookup=fake_lookup,
            )

        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["required_failures"], [])

    def test_missing_models_are_required_when_requested(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "third_party" / "daVinci-MagiHuman"
            repo.mkdir(parents=True)

            report = build_preflight(
                project_root=root,
                repo_dir=repo,
                model_root=root / "models",
                mode="container",
                require_models=True,
                min_disk_gib=0,
                command_lookup=fake_lookup,
            )

        self.assertEqual(report["status"], "not_ready")
        self.assertIn("model root", [item["name"] for item in report["required_failures"]])

    def test_markdown_contains_status_and_commands(self):
        report = build_preflight(min_disk_gib=0, command_lookup=fake_lookup)
        text = markdown_preflight(report)

        self.assertIn("# GPU Preflight", text)
        self.assertIn("nvidia-smi", text)
        self.assertIn("Status:", text)


if __name__ == "__main__":
    unittest.main()
