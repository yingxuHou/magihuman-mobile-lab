import tempfile
import unittest
from pathlib import Path

from backend.evidence_package import build_manifest, markdown_manifest


class EvidencePackageTest(unittest.TestCase):
    def test_manifest_reports_ok_for_small_evidence_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir()
            (root / "logs" / "P01_metrics.json").write_text("{}", encoding="utf-8")
            (root / "outputs" / "reports").mkdir(parents=True)
            (root / "outputs" / "reports" / "report.md").write_text("# Report", encoding="utf-8")

            manifest = build_manifest(root)

        self.assertEqual(manifest["status"], "ok")
        self.assertEqual(manifest["file_count"], 2)
        self.assertEqual(manifest["by_top_level"]["logs"], 1)

    def test_manifest_flags_forbidden_media(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "outputs").mkdir()
            (root / "outputs" / "sample.mp4").write_bytes(b"not a real video")

            manifest = build_manifest(root)

        self.assertEqual(manifest["status"], "contains_forbidden_files")
        self.assertEqual(manifest["forbidden_files"][0]["path"], "outputs/sample.mp4")

    def test_markdown_manifest_contains_file_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "evidence.json").write_text("{}", encoding="utf-8")
            text = markdown_manifest(build_manifest(root))

        self.assertIn("# GPU Evidence Package Manifest", text)
        self.assertIn("evidence.json", text)

    def test_package_script_includes_provenance_and_p01_manifest(self):
        text = Path("scripts/package_gpu_evidence.sh").read_text(encoding="utf-8")

        self.assertIn("docs/p01-smoke-manifest.json", text)
        self.assertIn("docs/p01-smoke-manifest.md", text)
        self.assertIn("backend.evidence_provenance", text)
        self.assertIn("evidence-provenance.json", text)


if __name__ == "__main__":
    unittest.main()
