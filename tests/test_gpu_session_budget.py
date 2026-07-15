import json
import tempfile
import unittest
from pathlib import Path

from backend.gpu_session_budget import (
    build_budget_template,
    build_session_budget_report,
    expected_checkpoint_gib,
    markdown_budget_report,
)


def write_budget_config(root, **overrides):
    config = build_budget_template()
    config.update(
        {
            "gpu_provider": "Example GPU Cloud",
            "gpu_name": "NVIDIA H100",
            "gpu_hourly_usd": 8.0,
            "max_session_hours": 2.0,
            "max_session_budget_usd": 25.0,
            "disk_budget_gib": 300.0,
        }
    )
    config.update(overrides)
    path = Path(root) / "gpu-session-budget.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


class GpuSessionBudgetTest(unittest.TestCase):
    def test_template_contains_required_budget_fields(self):
        template = build_budget_template()

        self.assertEqual(template["checkpoint_profile"], "p01")
        self.assertIn("gpu_hourly_usd", template)
        self.assertIn("max_session_budget_usd", template)
        self.assertIn("disk_budget_gib", template)

    def test_missing_config_is_not_ready(self):
        report = build_session_budget_report("does-not-exist.json")

        self.assertEqual(report["status"], "missing_budget_config")
        self.assertIn("missing", report["summary"])

    def test_incomplete_config_lists_missing_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "gpu-session-budget.json"
            path.write_text(json.dumps(build_budget_template()), encoding="utf-8")

            report = build_session_budget_report(path)

        self.assertEqual(report["status"], "incomplete_budget_config")
        self.assertIn("gpu_hourly_usd", report["missing_fields"])
        self.assertIn("max_session_hours", report["missing_fields"])

    def test_invalid_config_lists_invalid_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_budget_config(tmp, gpu_hourly_usd=-1.0)

            report = build_session_budget_report(path)

        self.assertEqual(report["status"], "invalid_budget_config")
        self.assertIn("gpu_hourly_usd", report["invalid_fields"])

    def test_budget_ready_when_cost_and_disk_are_within_caps(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_budget_config(tmp)

            report = build_session_budget_report(path)

        self.assertEqual(report["status"], "budget_ready")
        self.assertEqual(report["estimated_session_cost_usd"], 20.0)
        self.assertGreater(report["budget_headroom_usd"], 0)

    def test_over_budget_blocks_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_budget_config(tmp, max_session_budget_usd=10.0)

            report = build_session_budget_report(path)

        self.assertEqual(report["status"], "budget_exceeded")

    def test_disk_budget_too_low_blocks_required_suite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_budget_config(tmp, checkpoint_profile="required_suite", disk_budget_gib=200.0)

            report = build_session_budget_report(path)

        self.assertEqual(report["status"], "disk_budget_too_low")
        self.assertGreater(expected_checkpoint_gib("required_suite"), 200.0)

    def test_markdown_lists_stop_rules(self):
        text = markdown_budget_report(build_session_budget_report(None))

        self.assertIn("# GPU Session Budget Guard", text)
        self.assertIn("Do not start the GPU session", text)

    def test_wrapper_scripts_call_budget_module(self):
        bash_text = Path("scripts/generate_gpu_session_budget.sh").read_text(encoding="utf-8")
        ps1_text = Path("scripts/generate_gpu_session_budget.ps1").read_text(encoding="utf-8")

        self.assertIn("backend.gpu_session_budget", bash_text)
        self.assertIn("backend.gpu_session_budget", ps1_text)


if __name__ == "__main__":
    unittest.main()
