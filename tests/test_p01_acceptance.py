import json
import tempfile
import unittest
from pathlib import Path

from backend.p01_acceptance import build_p01_acceptance, markdown_p01_acceptance
from tests.test_feasibility_decision import sample_metrics
from tests.test_metrics_context_audit import find_case, matching_run_context, write_p01_manifest


def write_p01_metrics(log_dir, manifest, video_updates=None):
    case = find_case("P01")
    payload = sample_metrics()
    payload["run"] = matching_run_context(case, manifest_path=manifest)
    if video_updates:
        payload["video"].update(video_updates)
    path = Path(log_dir) / "P01_test_metrics.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def touch_result(root):
    result = Path(root) / "outputs" / "smoke-test" / "P01.mp4"
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_bytes(b"fake mp4 placeholder")
    return result


class P01AcceptanceTest(unittest.TestCase):
    def test_missing_metrics_blocks_full_suite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_p01_acceptance(
                log_dir=root / "logs",
                result_path=root / "outputs" / "smoke-test" / "P01.mp4",
                p01_manifest_path=root / "p01-smoke-manifest.json",
            )

        self.assertEqual(report["status"], "not_ready")
        self.assertTrue(any(check["label"] == "P01 runtime metrics measured" for check in report["failures"]))

    def test_matching_p01_evidence_is_ready_for_full_suite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_dir = root / "logs"
            manifest = write_p01_manifest(root)
            write_p01_metrics(log_dir, manifest)
            result = touch_result(root)

            report = build_p01_acceptance(log_dir=log_dir, result_path=result, p01_manifest_path=manifest)

        self.assertEqual(report["status"], "ready_for_full_suite")
        self.assertEqual(report["failures"], [])

    def test_mobile_transcode_need_still_allows_full_suite_with_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_dir = root / "logs"
            manifest = write_p01_manifest(root)
            write_p01_metrics(log_dir, manifest, video_updates={"video_codec_name": "hevc"})
            result = touch_result(root)

            report = build_p01_acceptance(log_dir=log_dir, result_path=result, p01_manifest_path=manifest)

        self.assertEqual(report["status"], "ready_for_full_suite_with_transcode_required")
        self.assertEqual(report["failures"], [])
        self.assertEqual(report["mobile_video_status"], "mobile_video_needs_transcode")

    def test_duration_outside_tolerance_blocks_full_suite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_dir = root / "logs"
            manifest = write_p01_manifest(root)
            write_p01_metrics(log_dir, manifest, video_updates={"duration_seconds": 12.0})
            result = touch_result(root)

            report = build_p01_acceptance(log_dir=log_dir, result_path=result, p01_manifest_path=manifest)

        self.assertEqual(report["status"], "not_ready")
        self.assertTrue(any(check["label"] == "P01 video duration near target" for check in report["failures"]))

    def test_markdown_explains_proceed_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_dir = root / "logs"
            manifest = write_p01_manifest(root)
            write_p01_metrics(log_dir, manifest)
            result = touch_result(root)
            text = markdown_p01_acceptance(build_p01_acceptance(log_dir=log_dir, result_path=result, p01_manifest_path=manifest))

        self.assertIn("# P01 Smoke Acceptance", text)
        self.assertIn("`ready_for_full_suite`", text)
        self.assertIn("proceed", text)


if __name__ == "__main__":
    unittest.main()
