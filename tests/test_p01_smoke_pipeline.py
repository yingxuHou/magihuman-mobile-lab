import unittest
from pathlib import Path


class P01SmokePipelineTest(unittest.TestCase):
    def test_script_targets_only_p01_case(self):
        text = Path("scripts/run_p01_smoke_pipeline.sh").read_text(encoding="utf-8")

        self.assertIn("--cases P01", text)
        self.assertNotIn("--cases P03", text)
        self.assertNotIn("--cases P04", text)

    def test_script_keeps_gpu_first_run_gates(self):
        text = Path("scripts/run_p01_smoke_pipeline.sh").read_text(encoding="utf-8")

        self.assertIn("scripts/prepare_sources.sh", text)
        self.assertIn("--require-hf-auth", text)
        self.assertIn("backend.hf_access_audit --profile p01", text)
        self.assertIn("scripts/download_models.sh", text)
        self.assertIn("backend.experiment_results", text)
        self.assertIn("backend.feasibility_decision", text)


if __name__ == "__main__":
    unittest.main()
