import json
import tempfile
import unittest
from pathlib import Path

from backend.cost_review import build_cost_report, build_cost_template, cost_for_wall_time, markdown_cost_report
from tests.test_feasibility_decision import sample_metrics, write_required_metrics


def write_cost_review(root, max_cost=1.0, max_wall=10.0):
    review = build_cost_template()
    review["gpu_name"] = "NVIDIA H100"
    review["gpu_hourly_usd"] = 8.0
    review["billing_overhead_multiplier"] = 1.25
    review["max_cost_per_video_usd"] = max_cost
    review["max_wall_time_seconds"] = max_wall
    path = Path(root) / "cost_review.json"
    path.write_text(json.dumps(review), encoding="utf-8")
    return path


class CostReviewTest(unittest.TestCase):
    def test_cost_for_wall_time(self):
        self.assertAlmostEqual(cost_for_wall_time(360, 10, 1.0), 1.0)

    def test_template_contains_required_fields(self):
        template = build_cost_template()

        self.assertIn("gpu_hourly_usd", template)
        self.assertEqual(template["case_ids"], ["P01", "P03", "P04", "T01", "T02"])

    def test_missing_review_file(self):
        report = build_cost_report("does-not-exist.json", log_dir="does-not-exist")

        self.assertEqual(report["status"], "missing_cost_review")
        self.assertIn("missing", report["summary"])

    def test_incomplete_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cost_review.json"
            path.write_text(json.dumps(build_cost_template()), encoding="utf-8")

            report = build_cost_report(path, log_dir=tmp)

        self.assertEqual(report["status"], "incomplete_cost_review")
        self.assertIn("gpu_hourly_usd", report["missing_fields"])

    def test_passing_cost_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_required_metrics(root)
            path = write_cost_review(root)

            report = build_cost_report(path, log_dir=root)

        self.assertEqual(report["status"], "cost_review_passed")
        self.assertTrue(all(row["status"] == "passed" for row in report["rows"]))

    def test_failed_cost_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for case_id in ["P01", "P03", "P04", "T01", "T02"]:
                (root / "{}_test_metrics.json".format(case_id)).write_text(
                    json.dumps(sample_metrics(wall=20.0)), encoding="utf-8"
                )
            path = write_cost_review(root, max_cost=0.001, max_wall=10.0)

            report = build_cost_report(path, log_dir=root)

        self.assertEqual(report["status"], "cost_review_failed")
        self.assertEqual(report["rows"][0]["latency_status"], "failed")

    def test_markdown_cost_report(self):
        text = markdown_cost_report(build_cost_report(None, log_dir="does-not-exist"))

        self.assertIn("# Cost Review", text)
        self.assertIn("missing_cost_review", text)


if __name__ == "__main__":
    unittest.main()
