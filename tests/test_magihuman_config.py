import json
import tempfile
import unittest
from pathlib import Path

from backend.magihuman_config import build_config, get_profile, shell_exports


class MagiHumanConfigTest(unittest.TestCase):
    def create_repo(self, root):
        repo = root / "repo"
        for name in ("base", "distill", "sr_540p", "sr_1080p"):
            (repo / "example" / name).mkdir(parents=True, exist_ok=True)

        base_config = {
            "engine_config": {"load": "/old", "cp_size": 1},
            "evaluation_config": {
                "audio_model_path": "/old",
                "txt_model_path": "/old",
                "vae_model_path": "/old",
                "use_turbo_vae": True,
                "student_config_path": "/old",
                "student_ckpt_path": "/old",
            },
        }
        sr_config = json.loads(json.dumps(base_config))
        sr_config["evaluation_config"]["use_sr_model"] = True
        sr_config["evaluation_config"]["sr_model_path"] = "/old"

        for name in ("base", "distill"):
            (repo / "example" / name / "config.json").write_text(json.dumps(base_config), encoding="utf-8")
        for name in ("sr_540p", "sr_1080p"):
            (repo / "example" / name / "config.json").write_text(json.dumps(sr_config), encoding="utf-8")
        return repo

    def test_build_base_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self.create_repo(root)
            metadata = build_config(repo, root / "models", root / "configs", "256p", "base", cp_size=2)
            config = json.loads(Path(metadata["config_path"]).read_text(encoding="utf-8"))

            self.assertEqual(metadata["br_width"], 448)
            self.assertEqual(metadata["br_height"], 256)
            self.assertEqual(config["engine_config"]["cp_size"], 2)
            load_path = config["engine_config"]["load"].replace("\\", "/")
            txt_path = config["evaluation_config"]["txt_model_path"].replace("\\", "/")
            self.assertTrue(load_path.endswith("daVinci-MagiHuman/base"))
            self.assertTrue(txt_path.endswith("t5gemma-9b-9b-ul2"))

    def test_build_1080p_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self.create_repo(root)
            metadata = build_config(repo, root / "models", root / "configs", "1080p", "base")
            config = json.loads(Path(metadata["config_path"]).read_text(encoding="utf-8"))

            self.assertEqual(metadata["sr_width"], 1920)
            self.assertEqual(metadata["sr_height"], 1088)
            sr_path = config["evaluation_config"]["sr_model_path"].replace("\\", "/")
            self.assertTrue(sr_path.endswith("daVinci-MagiHuman/1080p_sr"))

    def test_reject_distill_for_sr(self):
        with self.assertRaises(ValueError):
            get_profile("540p", "distill")

    def test_shell_exports(self):
        exports = shell_exports(
            {
                "config_path": "/tmp/config.json",
                "br_width": 448,
                "br_height": 256,
                "sr_width": None,
                "sr_height": None,
                "master_port": 6013,
                "variant": "base",
            }
        )
        self.assertIn("MAGIHUMAN_CONFIG_PATH=/tmp/config.json", exports)
        self.assertIn("MAGIHUMAN_SR_WIDTH=''", exports)


if __name__ == "__main__":
    unittest.main()
