import json
import tempfile
import unittest
from pathlib import Path

from backend.experiment_suite import REQUIRED_CASE_IDS
from backend.required_suite_acceptance import build_required_suite_acceptance, markdown_required_suite_acceptance
from tests.test_feasibility_decision import sample_metrics
from tests.test_metrics_context_audit import find_case, matching_run_context, write_p01_manifest


def write_case_metrics(log_dir, case_id, manifest=None, video_updates=None, seed=None):
    case = find_case(case_id)
    payload = sample_metrics()
    payload["run"] = matching_run_context(case, manifest_path=manifest, seed=seed)
    if video_updates:
        payload["video"].update(video_updates)
    path = Path(log_dir) / "{}_test_metrics.json".format(case_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def write_required_suite(root, video_updates_by_case=None, seed_by_case=None):
    video_updates_by_case = video_updates_by_case or {}
    seed_by_case = seed_by_case or {}
    log_dir = Path(root) / "logs"
    result_dir = Path(root) / "outputs" / "experiment-results"
    p01_result = Path(root) / "outputs" / "smoke-test" / "P01.mp4"
    manifest = write_p01_manifest(Path(root))
    for case_id in REQUIRED_CASE_IDS:
        write_case_metrics(
            log_dir,
            case_id,
            manifest=manifest if case_id == "P01" else None,
            video_updates=video_updates_by_case.get(case_id),
            seed=seed_by_case.get(case_id),
        )
        result = p01_result if case_id == "P01" else result_dir / "{}.mp4".format(case_id)
        result.parent.mkdir(parents=True, exist_ok=True)
        result.write_bytes(b"fake mp4 placeholder")
    return log_dir, result_dir, p01_result, manifest


class RequiredSuiteAcceptanceTest(unittest.TestCase):
    def test_missing_metrics_blocks_reviews(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_required_suite_acceptance(
                log_dir=root / "logs",
                result_dir=root / "outputs" / "experiment-results",
                p01_result_path=root / "outputs" / "smoke-test" / "P01.mp4",
                p01_manifest_path=root / "p01-smoke-manifest.json",
            )

        self.assertEqual(report["status"], "not_ready")
        self.assertTrue(any(failure["label"] == "runtime metrics measured" for failure in report["failures"]))

    def test_matching_required_suite_is_ready_for_reviews(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_dir, result_dir, p01_result, manifest = write_required_suite(Path(tmp))

            report = build_required_suite_acceptance(
                log_dir=log_dir,
                result_dir=result_dir,
                p01_result_path=p01_result,
                p01_manifest_path=manifest,
            )
            text = markdown_required_suite_acceptance(report)

        self.assertEqual(report["status"], "ready_for_quality_and_cost_review")
        self.assertEqual(report["failures"], [])
        self.assertIn("quality and cost review", text)

    def test_mobile_transcode_need_keeps_reviews_allowed_with_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_dir, result_dir, p01_result, manifest = write_required_suite(
                Path(tmp),
                video_updates_by_case={"T02": {"video_codec_name": "hevc"}},
            )

            report = build_required_suite_acceptance(
                log_dir=log_dir,
                result_dir=result_dir,
                p01_result_path=p01_result,
                p01_manifest_path=manifest,
            )

        self.assertEqual(report["status"], "ready_for_quality_and_cost_review_with_transcode_required")
        self.assertEqual(report["failures"], [])

    def test_missing_result_file_blocks_reviews(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_dir, result_dir, p01_result, manifest = write_required_suite(root)
            (result_dir / "P04.mp4").unlink()

            report = build_required_suite_acceptance(
                log_dir=log_dir,
                result_dir=result_dir,
                p01_result_path=p01_result,
                p01_manifest_path=manifest,
            )

        self.assertEqual(report["status"], "not_ready")
        self.assertTrue(any(row["case_id"] == "P04" and row["failures"] for row in report["rows"]))

    def test_context_mismatch_blocks_reviews(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_dir, result_dir, p01_result, manifest = write_required_suite(Path(tmp), seed_by_case={"T01": 7})

            report = build_required_suite_acceptance(
                log_dir=log_dir,
                result_dir=result_dir,
                p01_result_path=p01_result,
                p01_manifest_path=manifest,
            )

        self.assertEqual(report["status"], "not_ready")
        self.assertTrue(any(row["case_id"] == "T01" and row["context"]["status"] == "context_mismatch" for row in report["rows"]))


if __name__ == "__main__":
    unittest.main()
