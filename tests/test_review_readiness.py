import json
import tempfile
import unittest
from pathlib import Path

from backend.review_readiness import build_review_readiness, markdown_review_readiness
from tests.test_required_suite_acceptance import write_required_suite


class ReviewReadinessTest(unittest.TestCase):
    def test_missing_runtime_evidence_does_not_create_review_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            quality_path = root / "docs" / "quality-review.json"
            cost_path = root / "docs" / "cost-review.json"

            report = build_review_readiness(
                log_dir=root / "logs",
                result_dir=root / "outputs" / "experiment-results",
                p01_result_path=root / "outputs" / "smoke-test" / "P01.mp4",
                p01_manifest_path=root / "docs" / "p01-smoke-manifest.json",
                quality_review_path=quality_path,
                cost_review_path=cost_path,
                create_templates=True,
            )

            self.assertEqual(report["status"], "runtime_not_ready")
            self.assertEqual(report["created_files"], [])
            self.assertFalse(quality_path.exists())
            self.assertFalse(cost_path.exists())

    def test_ready_suite_creates_quality_and_cost_review_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_dir, result_dir, p01_result, manifest = write_required_suite(root)
            quality_path = root / "docs" / "quality-review.json"
            cost_path = root / "docs" / "cost-review.json"

            report = build_review_readiness(
                log_dir=log_dir,
                result_dir=result_dir,
                p01_result_path=p01_result,
                p01_manifest_path=manifest,
                quality_review_path=quality_path,
                cost_review_path=cost_path,
                create_templates=True,
            )

            self.assertEqual(report["status"], "review_inputs_ready")
            self.assertTrue(quality_path.is_file())
            self.assertTrue(cost_path.is_file())
            quality = json.loads(quality_path.read_text(encoding="utf-8"))
            cost = json.loads(cost_path.read_text(encoding="utf-8"))
            self.assertEqual(quality["case_reviews"][0]["sample_path"], str(p01_result))
            self.assertEqual(cost["case_ids"], ["P01", "P03", "P04", "T01", "T02"])

    def test_ready_suite_without_create_templates_reports_missing_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_dir, result_dir, p01_result, manifest = write_required_suite(root)

            report = build_review_readiness(
                log_dir=log_dir,
                result_dir=result_dir,
                p01_result_path=p01_result,
                p01_manifest_path=manifest,
                quality_review_path=root / "docs" / "quality-review.json",
                cost_review_path=root / "docs" / "cost-review.json",
            )

            self.assertEqual(report["status"], "review_inputs_missing")
            self.assertIn("Required-suite runtime evidence is ready", report["summary"])

    def test_existing_review_inputs_are_not_overwritten_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_dir, result_dir, p01_result, manifest = write_required_suite(root)
            quality_path = root / "docs" / "quality-review.json"
            cost_path = root / "docs" / "cost-review.json"
            quality_path.parent.mkdir(parents=True)
            quality_path.write_text('{"sentinel": "quality"}', encoding="utf-8")
            cost_path.write_text('{"sentinel": "cost"}', encoding="utf-8")

            report = build_review_readiness(
                log_dir=log_dir,
                result_dir=result_dir,
                p01_result_path=p01_result,
                p01_manifest_path=manifest,
                quality_review_path=quality_path,
                cost_review_path=cost_path,
                create_templates=True,
            )

            self.assertEqual(report["status"], "review_inputs_ready")
            self.assertEqual(report["created_files"], [])
            self.assertEqual(json.loads(quality_path.read_text(encoding="utf-8")), {"sentinel": "quality"})
            self.assertEqual(json.loads(cost_path.read_text(encoding="utf-8")), {"sentinel": "cost"})

    def test_markdown_warns_when_mobile_transcode_is_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_dir, result_dir, p01_result, manifest = write_required_suite(
                root,
                video_updates_by_case={"T02": {"video_codec_name": "hevc"}},
            )

            report = build_review_readiness(
                log_dir=log_dir,
                result_dir=result_dir,
                p01_result_path=p01_result,
                p01_manifest_path=manifest,
                quality_review_path=root / "docs" / "quality-review.json",
                cost_review_path=root / "docs" / "cost-review.json",
                create_templates=True,
            )
            text = markdown_review_readiness(report)

            self.assertEqual(report["status"], "review_inputs_ready")
            self.assertIn("transcode", text)

    def test_wrapper_script_runs_review_readiness_module(self):
        text = Path("scripts/prepare_review_inputs.sh").read_text(encoding="utf-8")

        self.assertIn("backend.review_readiness", text)
        self.assertIn("--create-templates", text)


if __name__ == "__main__":
    unittest.main()
