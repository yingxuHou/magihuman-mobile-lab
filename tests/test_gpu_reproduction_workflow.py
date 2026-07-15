import unittest
from pathlib import Path


class GpuReproductionWorkflowTest(unittest.TestCase):
    def read_script(self):
        return Path("scripts/run_gpu_reproduction_workflow.sh").read_text(encoding="utf-8")

    def test_workflow_runs_p01_before_full_and_package(self):
        text = self.read_script()

        self.assertLess(text.index("scripts/run_p01_smoke_pipeline.sh"), text.index("scripts/gpu_reproduction_pipeline.sh"))
        self.assertLess(text.index("scripts/gpu_reproduction_pipeline.sh"), text.index("scripts/package_gpu_evidence.sh"))

    def test_workflow_preserves_acceptance_gate_outputs(self):
        text = self.read_script()

        self.assertIn("backend.workflow_readiness_audit", text)
        self.assertIn("p01_acceptance_*.md", text)
        self.assertIn("required_suite_acceptance_*.md", text)
        self.assertIn("gpu_reproduction_workflow_", text)
        self.assertIn("UPSTREAM_DRIFT_AUDIT", text)

    def test_workflow_disables_nested_source_preparation_for_pipelines(self):
        text = self.read_script()

        self.assertIn("env PREPARE_SOURCES=0", text)
        self.assertIn("MODEL_PROFILE=p01", text)
        self.assertIn("MODEL_PROFILE=required_suite", text)


if __name__ == "__main__":
    unittest.main()
