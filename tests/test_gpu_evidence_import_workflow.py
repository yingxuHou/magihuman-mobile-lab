import tarfile
import tempfile
import unittest
from pathlib import Path

from backend.gpu_evidence_import_workflow import build_import_workflow_report, extract_archive


def make_archive(root, archive_name="gpu-evidence.tar.gz", include_forbidden=False):
    root = Path(root)
    package = root / "gpu-evidence-test"
    (package / "logs").mkdir(parents=True)
    (package / "docs").mkdir()
    (package / "outputs" / "reports").mkdir(parents=True)
    (package / "logs" / "P01_test_metrics.json").write_text("{}", encoding="utf-8")
    (package / "docs" / "p01-smoke-manifest.json").write_text("{}", encoding="utf-8")
    (package / "outputs" / "reports" / "report.md").write_text("# Report", encoding="utf-8")
    (package / "evidence-manifest.json").write_text("{}", encoding="utf-8")
    if include_forbidden:
        (package / "outputs" / "sample.mp4").write_bytes(b"video")
    archive = root / archive_name
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(package, arcname=package.name)
    return archive


class GpuEvidenceImportWorkflowTest(unittest.TestCase):
    def test_imports_allowed_package_files_and_writes_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = make_archive(root)
            project = root / "project"
            project.mkdir()
            (project / "docs").mkdir()
            manifest = Path("docs/p01-smoke-manifest.json").read_text(encoding="utf-8")
            (project / "docs" / "p01-smoke-manifest.json").write_text(manifest, encoding="utf-8")

            report = build_import_workflow_report(archive, project_root=project)

            self.assertEqual(report["status"], "imported_incomplete")
            self.assertIn("logs/P01_test_metrics.json", report["imported_files"])
            self.assertTrue((project / "docs" / "gpu-evidence-import-audit.md").is_file())
            self.assertTrue((project / "docs" / "mobile-feasibility-report.md").is_file())
            self.assertTrue((project / "docs" / "review-readiness.md").is_file())
            self.assertTrue((project / "docs" / "reproduction-gap-report.md").is_file())
            self.assertEqual(report["review_readiness_status"], "runtime_not_ready")
            self.assertEqual(report["gap_report_status"], "handoff_not_ready")

    def test_forbidden_media_package_is_not_imported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = make_archive(root, include_forbidden=True)
            project = root / "project"
            project.mkdir()

            report = build_import_workflow_report(archive, project_root=project)

        self.assertEqual(report["status"], "package_not_imported")
        self.assertEqual(report["imported_files"], [])
        self.assertIsNone(report["gap_report_status"])

    def test_unsafe_archive_member_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "unsafe.tar.gz"
            payload = root / "payload.txt"
            payload.write_text("x", encoding="utf-8")
            with tarfile.open(archive, "w:gz") as tar:
                tar.add(payload, arcname="../payload.txt")

            with self.assertRaises(ValueError):
                extract_archive(archive, extract_root=root / "extract")


if __name__ == "__main__":
    unittest.main()
