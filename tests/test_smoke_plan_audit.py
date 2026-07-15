import copy
import unittest
from pathlib import Path

from backend.smoke_manifest import build_p01_manifest
from backend.smoke_plan_audit import build_smoke_plan_audit, markdown_smoke_plan_audit


class SmokePlanAuditTest(unittest.TestCase):
    def test_default_manifest_matches_p01_plan(self):
        manifest = build_p01_manifest()

        report = build_smoke_plan_audit(manifest=manifest)

        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["failures"], [])

    def test_changed_result_dir_detects_mismatch(self):
        manifest = build_p01_manifest()

        report = build_smoke_plan_audit(manifest=manifest, result_dir="outputs/other")

        self.assertEqual(report["status"], "not_ready")
        self.assertIn("expected_result_path", [item["label"] for item in report["failures"]])

    def test_changed_seed_detects_mismatch(self):
        manifest = build_p01_manifest()
        manifest = copy.deepcopy(manifest)
        manifest["actual_p01_inputs"]["seed"] = 7
        manifest["actual_p01_inputs"]["runner_env"]["MAGIHUMAN_SEED"] = "7"

        report = build_smoke_plan_audit(manifest=manifest)

        self.assertEqual(report["status"], "not_ready")
        self.assertIn("seed", [item["label"] for item in report["failures"]])
        self.assertIn("env.MAGIHUMAN_SEED", [item["label"] for item in report["failures"]])

    def test_markdown_contains_status_and_result_path(self):
        report = build_smoke_plan_audit(manifest=build_p01_manifest())
        text = markdown_smoke_plan_audit(report)

        self.assertIn("# P01 Smoke Plan Audit", text)
        self.assertIn("`ready`", text)
        self.assertIn("outputs/smoke-test/P01.mp4", text)

    def test_scripts_include_smoke_plan_audit(self):
        p01 = Path("scripts/run_p01_smoke_pipeline.sh").read_text(encoding="utf-8")
        package = Path("scripts/package_gpu_evidence.sh").read_text(encoding="utf-8")

        self.assertIn("backend.smoke_plan_audit", p01)
        self.assertIn("p01_smoke_plan_audit_", p01)
        self.assertIn("*smoke_plan_audit*.json", package)


if __name__ == "__main__":
    unittest.main()
