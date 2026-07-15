import json
import tempfile
import unittest
from pathlib import Path

from backend.mobile_video_check import (
    build_log_dir_report,
    evaluate_video_info,
    markdown_report,
    transcode_command,
)
from tests.test_experiment_results import sample_metrics


def mobile_video_info(**overrides):
    video = {
        "duration_seconds": 5.0,
        "has_video": True,
        "has_audio": True,
        "width": 448,
        "height": 256,
        "video_codec_name": "h264",
        "video_pix_fmt": "yuv420p",
        "audio_codec_name": "aac",
        "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
        "size_bytes": 12 * 1024 * 1024,
    }
    video.update(overrides)
    return video


class MobileVideoCheckTest(unittest.TestCase):
    def test_h264_aac_mp4_is_mobile_ready(self):
        report = evaluate_video_info(mobile_video_info())

        self.assertEqual(report["status"], "mobile_video_ready")
        self.assertEqual(report["required_failures"], [])

    def test_non_mobile_codec_needs_transcode(self):
        report = evaluate_video_info(mobile_video_info(video_codec_name="vp9"))

        self.assertEqual(report["status"], "mobile_video_needs_transcode")
        self.assertIn("video_codec", [check["name"] for check in report["required_failures"]])

    def test_oversized_dimensions_are_not_ready(self):
        report = evaluate_video_info(mobile_video_info(width=3840, height=2160))

        self.assertEqual(report["status"], "mobile_video_not_ready")
        self.assertIn("dimensions", [check["name"] for check in report["required_failures"]])

    def test_log_dir_report_marks_missing_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_log_dir_report(log_dir=tmp, case_ids=["P01"])

        self.assertEqual(report["status"], "missing_mobile_video_evidence")
        self.assertEqual(report["rows"][0]["status"], "missing_video_metrics")

    def test_log_dir_report_uses_metrics_video_info(self):
        with tempfile.TemporaryDirectory() as tmp:
            metrics = sample_metrics()
            metrics["video"].update(mobile_video_info())
            Path(tmp, "P01_test_metrics.json").write_text(json.dumps(metrics), encoding="utf-8")

            report = build_log_dir_report(log_dir=tmp, case_ids=["P01"])

        self.assertEqual(report["status"], "mobile_video_ready")
        self.assertEqual(report["rows"][0]["status"], "mobile_video_ready")

    def test_markdown_and_transcode_command(self):
        report = {
            "status": "mobile_video_needs_transcode",
            "source": "logs",
            "rows": [
                {
                    "case_id": "P01",
                    "metrics_path": "logs/P01_metrics.json",
                    "status": "mobile_video_needs_transcode",
                    "required_failures": [{"name": "video_codec"}],
                    "transcode_command": transcode_command("outputs/P01.webm", "outputs/P01_mobile.mp4"),
                }
            ],
        }
        text = markdown_report(report)

        self.assertIn("# Mobile Video Compatibility", text)
        self.assertIn("video_codec", text)
        self.assertIn("ffmpeg", text)


if __name__ == "__main__":
    unittest.main()
