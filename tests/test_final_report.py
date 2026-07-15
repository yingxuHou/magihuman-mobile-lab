import tempfile
import unittest
from pathlib import Path

from backend.final_report import build_final_report, demote_headings, markdown_final_report, report_status
from tests.test_feasibility_decision import write_cost_review, write_quality_review, write_required_metrics


class FinalReportTest(unittest.TestCase):
    def test_report_is_incomplete_when_runtime_metrics_are_missing(self):
        report = build_final_report(log_dir="does-not-exist")

        self.assertEqual(report["status"], "incomplete_runtime_evidence")
        self.assertEqual(report["recommendation"], "B_pending_runtime")
        self.assertEqual(report["evidence_gates"][1]["status"], "insufficient_runtime_evidence")

    def test_report_ready_when_all_gates_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_required_metrics(root)
            quality_path = write_quality_review(root, passing=True)
            cost_path = write_cost_review(root, passing=True)

            report = build_final_report(log_dir=root, quality_review_path=quality_path, cost_review_path=cost_path)

        self.assertEqual(report["status"], "cloud_candidate_ready_for_product_review")
        self.assertEqual(report["recommendation"], "B_candidate_ready_for_product_review")

    def test_report_status_stop_candidate(self):
        self.assertEqual(report_status({"recommendation": "C_candidate_cost_failed"}), "stop_candidate")

    def test_markdown_report_contains_sections(self):
        text = markdown_final_report(build_final_report(log_dir="does-not-exist"))

        self.assertIn("# Final Mobile Feasibility Report", text)
        self.assertIn("## Evidence Gates", text)
        self.assertIn("### Mobile Feasibility Decision", text)
        self.assertIn("## Runtime Metrics", text)
        self.assertIn("## Quality Review", text)
        self.assertIn("## Cost Review", text)

    def test_demote_headings(self):
        self.assertEqual(demote_headings("# A\n## B", levels=2), "### A\n#### B")


if __name__ == "__main__":
    unittest.main()
