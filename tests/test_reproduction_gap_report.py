import tempfile
import unittest
from pathlib import Path

from backend.reproduction_gap_report import build_reproduction_gap_report, markdown_gap_report
from tests.test_feasibility_decision import write_cost_review, write_quality_review
from tests.test_required_suite_acceptance import write_required_suite


class ReproductionGapReportTest(unittest.TestCase):
    def test_current_missing_budget_blocks_gpu_handoff(self):
        report = build_reproduction_gap_report(log_dir="does-not-exist")

        self.assertEqual(report["status"], "handoff_not_ready")
        self.assertEqual(report["recommendation"], "B_pending_runtime")
        self.assertEqual(report["gpu_execution_packet_status"], "attention_required")
        self.assertEqual(report["gpu_session_budget_status"], "incomplete_budget_config")
        self.assertEqual(report["missing_required_runtime_cases"], ["P01", "P03", "P04", "T01", "T02"])
        self.assertTrue(any(item["gate"] == "GPU session budget guard" for item in report["gaps"]))
        self.assertTrue(any(item["gate"] == "Required GPU runtime metrics" for item in report["gaps"]))

    def test_runtime_ready_without_templates_waits_for_review_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_dir, result_dir, p01_result, manifest = write_required_suite(root)

            report = build_reproduction_gap_report(
                log_dir=log_dir,
                result_dir=result_dir,
                p01_result_path=p01_result,
                p01_manifest_path=manifest,
                quality_review_path=root / "docs" / "quality-review.json",
                cost_review_path=root / "docs" / "cost-review.json",
            )

        self.assertEqual(report["status"], "awaiting_review_inputs")
        self.assertEqual(report["required_suite_acceptance_status"], "ready_for_quality_and_cost_review")
        self.assertEqual(report["review_readiness_status"], "review_inputs_missing")

    def test_all_required_evidence_makes_final_decision_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_dir, result_dir, p01_result, manifest = write_required_suite(root)
            quality_path = write_quality_review(root, passing=True)
            cost_path = write_cost_review(root, passing=True)

            report = build_reproduction_gap_report(
                log_dir=log_dir,
                result_dir=result_dir,
                p01_result_path=p01_result,
                p01_manifest_path=manifest,
                quality_review_path=quality_path,
                cost_review_path=cost_path,
            )

        self.assertEqual(report["status"], "final_decision_ready")
        self.assertEqual(report["final_report_status"], "cloud_candidate_ready_for_product_review")
        self.assertEqual(report["gaps"], [])

    def test_markdown_report_lists_open_gaps_and_decision_rule(self):
        text = markdown_gap_report(build_reproduction_gap_report(log_dir="does-not-exist"))

        self.assertIn("# Reproduction Gap Report", text)
        self.assertIn("GPU session budget", text)
        self.assertIn("Required GPU runtime metrics", text)
        self.assertIn("final mobile App recommendation remains provisional", text)


if __name__ == "__main__":
    unittest.main()
