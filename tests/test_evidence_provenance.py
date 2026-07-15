import tempfile
import unittest
from pathlib import Path

from backend.evidence_provenance import build_provenance, markdown_provenance


class EvidenceProvenanceTest(unittest.TestCase):
    def test_build_provenance_records_manifest_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            manifest = root / "docs" / "p01-smoke-manifest.json"
            manifest.write_text('{"case":"P01"}', encoding="utf-8")

            provenance = build_provenance(project_root=root, p01_manifest_path=manifest)

        self.assertEqual(provenance["status"], "attention_required")
        self.assertIn("missing_project_commit", provenance["blockers"])
        self.assertTrue(provenance["artifacts"]["p01_smoke_manifest"]["exists"])
        self.assertIn("sha256", provenance["artifacts"]["p01_smoke_manifest"])

    def test_markdown_provenance_contains_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            manifest = root / "docs" / "p01-smoke-manifest.json"
            manifest.write_text("{}", encoding="utf-8")
            text = markdown_provenance(build_provenance(project_root=root, p01_manifest_path=manifest))

        self.assertIn("# GPU Evidence Provenance", text)
        self.assertIn("## Official Sources", text)
        self.assertIn("p01_smoke_manifest", text)


if __name__ == "__main__":
    unittest.main()
