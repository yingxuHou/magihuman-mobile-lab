import tempfile
import unittest
import json
from pathlib import Path

from backend.evidence_import import build_import_audit, markdown_import_audit, missing_evidence
from tests.test_feasibility_decision import write_cost_review, write_quality_review, write_required_metrics


class EvidenceImportTest(unittest.TestCase):
    def test_missing_runtime_evidence_is_incomplete(self):
        audit = build_import_audit(log_dir="does-not-exist")

        self.assertEqual(audit["status"], "incomplete_import")
        self.assertEqual(audit["final_report_status"], "incomplete_runtime_evidence")
        self.assertEqual(audit["missing_evidence"][0]["gate"], "runtime")

    def test_complete_evidence_is_ready_for_final_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_required_metrics(root)
            quality_path = write_quality_review(root, passing=True)
            cost_path = write_cost_review(root, passing=True)

            audit = build_import_audit(log_dir=root, quality_review_path=quality_path, cost_review_path=cost_path)

        self.assertEqual(audit["status"], "ready_for_final_update")
        self.assertEqual(audit["final_report_status"], "cloud_candidate_ready_for_product_review")
        self.assertEqual(audit["missing_evidence"], [])

    def test_quality_failure_is_ready_for_final_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_required_metrics(root)
            quality_path = write_quality_review(root, passing=False)
            cost_path = write_cost_review(root, passing=True)

            audit = build_import_audit(log_dir=root, quality_review_path=quality_path, cost_review_path=cost_path)

        self.assertEqual(audit["status"], "ready_for_final_update")
        self.assertEqual(audit["final_report_status"], "stop_candidate")

    def test_missing_evidence_lists_quality_and_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_required_metrics(root)
            audit = build_import_audit(log_dir=root)

        gates = [item["gate"] for item in missing_evidence(audit["final_report"])]
        self.assertEqual(gates, ["quality", "cost"])

    def test_missing_mobile_video_evidence_is_listed(self):
        audit = build_import_audit(log_dir="does-not-exist")

        gates = [item["gate"] for item in audit["missing_evidence"]]
        self.assertIn("mobile_video", gates)

    def test_metrics_context_mismatch_blocks_final_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_required_metrics(root)
            p01_metrics = root / "P01_test_metrics.json"
            payload = json.loads(p01_metrics.read_text(encoding="utf-8"))
            payload["run"]["seed"] = 7
            p01_metrics.write_text(json.dumps(payload), encoding="utf-8")
            quality_path = write_quality_review(root, passing=True)
            cost_path = write_cost_review(root, passing=True)

            audit = build_import_audit(log_dir=root, quality_review_path=quality_path, cost_review_path=cost_path)

        gates = [item["gate"] for item in audit["missing_evidence"]]
        self.assertEqual(audit["status"], "incomplete_import")
        self.assertIn("metrics_context", gates)

    def test_markdown_import_audit_contains_sections(self):
        text = markdown_import_audit(build_import_audit(log_dir="does-not-exist"))

        self.assertIn("# GPU Evidence Import Audit", text)
        self.assertIn("## Gate Statuses", text)
        self.assertIn("## Metrics Context Audit", text)
        self.assertIn("## Missing Evidence", text)


if __name__ == "__main__":
    unittest.main()
