import tempfile
import unittest
from pathlib import Path

from backend.model_audit import build_model_audit, directory_size_bytes, markdown_model_audit


P01_PATHS = [
    "daVinci-MagiHuman/base",
    "daVinci-MagiHuman/turbo_vae",
    "t5gemma-9b-9b-ul2",
    "stable-audio-open-1.0",
    "Wan2.2-TI2V-5B",
]


def create_tiny_model_tree(root, paths=P01_PATHS):
    for relative in paths:
        path = root / relative
        path.mkdir(parents=True, exist_ok=True)
        (path / "placeholder.bin").write_bytes(b"x" * 16)


class ModelAuditTest(unittest.TestCase):
    def test_directory_size_bytes_sums_nested_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a" / "b").mkdir(parents=True)
            (root / "a" / "one.bin").write_bytes(b"1234")
            (root / "a" / "b" / "two.bin").write_bytes(b"123456")

            self.assertEqual(directory_size_bytes(root / "a"), 10)

    def test_missing_model_root_is_not_ready(self):
        report = build_model_audit("does-not-exist", profile="p01")

        self.assertEqual(report["status"], "not_ready")
        self.assertEqual({row["status"] for row in report["rows"]}, {"missing"})

    def test_p01_profile_ready_when_groups_exist_and_threshold_scaled_to_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_tiny_model_tree(root)

            report = build_model_audit(root, profile="p01", min_size_scale=0)

        self.assertEqual(report["status"], "ready")
        self.assertEqual(len(report["rows"]), 5)

    def test_tiny_files_fail_default_size_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_tiny_model_tree(root)

            report = build_model_audit(root, profile="p01")

        self.assertEqual(report["status"], "not_ready")
        self.assertIn("too_small", {row["status"] for row in report["rows"]})

    def test_required_suite_includes_sr_groups(self):
        report = build_model_audit("does-not-exist", profile="required_suite")

        self.assertIn("sr_540p", report["groups"])
        self.assertIn("sr_1080p", report["groups"])

    def test_markdown_contains_group_table(self):
        text = markdown_model_audit(build_model_audit("does-not-exist", profile="p01"))

        self.assertIn("# Model Checkpoint Audit", text)
        self.assertIn("| base | `missing` |", text)


if __name__ == "__main__":
    unittest.main()
