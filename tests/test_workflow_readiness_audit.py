import tempfile
import unittest
from pathlib import Path

from backend.workflow_readiness_audit import build_workflow_readiness_audit, markdown_workflow_readiness_audit


class WorkflowReadinessAuditTest(unittest.TestCase):
    def test_current_workflow_is_ready(self):
        audit = build_workflow_readiness_audit()

        self.assertEqual(audit["status"], "ready")
        self.assertEqual(audit["failures"], [])

    def test_missing_workflow_script_is_not_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()

            audit = build_workflow_readiness_audit(project_root=root)

        self.assertEqual(audit["status"], "not_ready")
        self.assertTrue(any(item["label"] == "workflow script exists" for item in audit["failures"]))

    def test_markdown_lists_workflow_checks(self):
        text = markdown_workflow_readiness_audit(build_workflow_readiness_audit())

        self.assertIn("# GPU Workflow Readiness Audit", text)
        self.assertIn("workflow order is P01 before full suite before package", text)
        self.assertIn("`ready`", text)


if __name__ == "__main__":
    unittest.main()
