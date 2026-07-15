import unittest

from backend.download_log_audit import build_download_log_audit, markdown_download_log_audit


P01_LOG = """
Downloading daVinci-MagiHuman P01 groups to models/daVinci-MagiHuman
download_command=huggingface-cli download GAIR/daVinci-MagiHuman --include base/\\* --include turbo_vae/\\* --local-dir models/daVinci-MagiHuman
Downloading text encoder to models/t5gemma-9b-9b-ul2
download_command=huggingface-cli download google/t5gemma-9b-9b-ul2 --local-dir models/t5gemma-9b-9b-ul2
Downloading audio model to models/stable-audio-open-1.0
download_command=huggingface-cli download stabilityai/stable-audio-open-1.0 --local-dir models/stable-audio-open-1.0
Downloading VAE to models/Wan2.2-TI2V-5B
download_command=huggingface-cli download Wan-AI/Wan2.2-TI2V-5B --local-dir models/Wan2.2-TI2V-5B
"""

REQUIRED_SUITE_LOG = """
download_command=huggingface-cli download GAIR/daVinci-MagiHuman --include base/\\* --include turbo_vae/\\* --include 540p_sr/\\* --include 1080p_sr/\\* --local-dir models/daVinci-MagiHuman
download_command=huggingface-cli download google/t5gemma-9b-9b-ul2 --local-dir models/t5gemma-9b-9b-ul2
download_command=huggingface-cli download stabilityai/stable-audio-open-1.0 --local-dir models/stable-audio-open-1.0
download_command=huggingface-cli download Wan-AI/Wan2.2-TI2V-5B --local-dir models/Wan2.2-TI2V-5B
"""


class DownloadLogAuditTest(unittest.TestCase):
    def test_p01_log_is_ready_without_sr_or_distill(self):
        report = build_download_log_audit(profile="p01", log_text=P01_LOG)

        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["failures"], [])

    def test_p01_log_fails_when_sr_group_is_requested(self):
        bad_log = P01_LOG.replace("--include turbo_vae/\\*", "--include turbo_vae/\\* --include 540p_sr/\\*")

        report = build_download_log_audit(profile="p01", log_text=bad_log)

        self.assertEqual(report["status"], "not_ready")
        self.assertIn("main group 540p_sr not requested", [item["label"] for item in report["failures"]])

    def test_required_suite_log_allows_sr_but_not_distill(self):
        report = build_download_log_audit(profile="required_suite", log_text=REQUIRED_SUITE_LOG)

        self.assertEqual(report["status"], "ready")

    def test_missing_external_repo_fails(self):
        report = build_download_log_audit(
            profile="p01",
            log_text=P01_LOG.replace("download_command=huggingface-cli download Wan-AI/Wan2.2-TI2V-5B --local-dir models/Wan2.2-TI2V-5B", ""),
        )

        self.assertEqual(report["status"], "not_ready")
        self.assertIn(
            "external repo Wan-AI/Wan2.2-TI2V-5B requested",
            [item["label"] for item in report["failures"]],
        )

    def test_markdown_contains_profile_and_status(self):
        text = markdown_download_log_audit(build_download_log_audit(profile="p01", log_text=P01_LOG))

        self.assertIn("# Download Log Audit", text)
        self.assertIn("Profile: `p01`", text)
        self.assertIn("Status: `ready`", text)


if __name__ == "__main__":
    unittest.main()
