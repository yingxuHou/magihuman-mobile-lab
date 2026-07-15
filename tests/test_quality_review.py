import json
import tempfile
import unittest
from pathlib import Path

from backend.quality_review import build_quality_report, build_review_template, markdown_quality_report


def passing_review():
    review = build_review_template()
    for item in review["case_reviews"]:
        item["playable_on_phone"] = True
        item["audio_video_sync_score"] = 4
        item["face_quality_score"] = 4
        item["motion_naturalness_score"] = 3
        item["speech_intelligibility_score"] = 4
        item["artifact_free_score"] = 3
    return review


class QualityReviewTest(unittest.TestCase):
    def test_template_contains_required_cases(self):
        template = build_review_template()

        self.assertEqual([item["case_id"] for item in template["case_reviews"]], ["P01", "P03", "P04", "T01", "T02"])
        self.assertEqual(template["case_reviews"][0]["sample_path"], "outputs/experiment-results/P01.mp4")

    def test_missing_review_file(self):
        report = build_quality_report("does-not-exist.json")

        self.assertEqual(report["status"], "missing_quality_review")
        self.assertIn("missing", report["summary"])

    def test_passing_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "quality.json"
            path.write_text(json.dumps(passing_review()), encoding="utf-8")

            report = build_quality_report(path)

        self.assertEqual(report["status"], "quality_review_passed")
        self.assertTrue(all(row["status"] == "passed" for row in report["rows"]))

    def test_failed_review(self):
        review = passing_review()
        review["case_reviews"][0]["face_quality_score"] = 2
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "quality.json"
            path.write_text(json.dumps(review), encoding="utf-8")

            report = build_quality_report(path)

        self.assertEqual(report["status"], "quality_review_failed")
        self.assertEqual(report["rows"][0]["failed_fields"], ["face_quality_score"])

    def test_incomplete_review_markdown(self):
        review = build_review_template()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "quality.json"
            path.write_text(json.dumps(review), encoding="utf-8")

            report = build_quality_report(path)
            text = markdown_quality_report(report)

        self.assertEqual(report["status"], "incomplete_quality_review")
        self.assertIn("playable_on_phone", text)


if __name__ == "__main__":
    unittest.main()
