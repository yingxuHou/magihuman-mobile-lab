import os
import shutil
import subprocess
import unittest
from pathlib import Path


class DownloadModelsScriptTest(unittest.TestCase):
    def run_script(self, **env_overrides):
        git_bash = Path("C:/Program Files/Git/bin/bash.exe")
        bash = str(git_bash) if git_bash.exists() else shutil.which("bash")
        if not bash:
            self.skipTest("bash is not available on PATH")
        env = os.environ.copy()
        env.update(env_overrides)
        return subprocess.run(
            [bash, "scripts/download_models.sh"],
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_script_defines_profiles(self):
        text = Path("scripts/download_models.sh").read_text(encoding="utf-8")

        self.assertIn("MODEL_PROFILE", text)
        self.assertIn("p01)", text)
        self.assertIn("required_suite)", text)
        self.assertIn("complete)", text)

    def test_p01_dry_run_downloads_only_base_and_turbo_main_groups(self):
        completed = self.run_script(MODEL_PROFILE="p01", DRY_RUN="1", MODEL_ROOT="models")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("base/\\*", completed.stdout)
        self.assertIn("turbo_vae/\\*", completed.stdout)
        self.assertNotIn("540p_sr/\\*", completed.stdout)
        self.assertNotIn("1080p_sr/\\*", completed.stdout)
        self.assertIn("google/t5gemma-9b-9b-ul2", completed.stdout)

    def test_required_suite_dry_run_includes_sr_but_not_distill(self):
        completed = self.run_script(MODEL_PROFILE="required_suite", DRY_RUN="1", MODEL_ROOT="models")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("540p_sr/\\*", completed.stdout)
        self.assertIn("1080p_sr/\\*", completed.stdout)
        self.assertNotIn("distill/\\*", completed.stdout)

    def test_unknown_profile_exits_nonzero(self):
        completed = self.run_script(MODEL_PROFILE="bad", DRY_RUN="1", MODEL_ROOT="models")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Unknown MODEL_PROFILE", completed.stderr)


if __name__ == "__main__":
    unittest.main()
