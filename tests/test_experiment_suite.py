import json
import tempfile
import unittest
from pathlib import Path

from backend.experiment_suite import (
    REQUIRED_CASE_IDS,
    build_suite_plan,
    default_case_ids,
    markdown_suite,
    suite_shell_text,
)
from tests.test_experiment_results import sample_metrics


class ExperimentSuiteTest(unittest.TestCase):
    def test_required_suite_order_is_ready_without_existing_metrics(self):
        suite = build_suite_plan(log_dir="does-not-exist")

        self.assertEqual(suite["status"], "ready")
        self.assertEqual([step["case_id"] for step in suite["steps"]], REQUIRED_CASE_IDS)
        self.assertTrue(all(step["action"] == "run" for step in suite["steps"]))

    def test_custom_case_blocks_when_dependencies_are_missing(self):
        suite = build_suite_plan(case_ids=["P04"], log_dir="does-not-exist")

        self.assertEqual(suite["status"], "blocked")
        self.assertEqual(suite["steps"][0]["action"], "blocked")
        self.assertEqual(suite["steps"][0]["missing_dependencies"], ["P01", "P03"])

    def test_measured_case_is_skipped_but_unmeasured_dependents_can_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "P01_test_metrics.json").write_text(json.dumps(sample_metrics()), encoding="utf-8")

            suite = build_suite_plan(log_dir=root)

        self.assertEqual(suite["steps"][0]["case_id"], "P01")
        self.assertEqual(suite["steps"][0]["action"], "skip_measured")
        self.assertEqual(suite["steps"][1]["case_id"], "P03")
        self.assertEqual(suite["steps"][1]["action"], "run")

    def test_include_optional_cases(self):
        self.assertEqual(default_case_ids(include_optional=True), ["P01", "P02", "P03", "P04", "T01", "T02", "T03", "T04"])

    def test_renderers_include_actions_and_commands(self):
        suite = build_suite_plan(log_dir="does-not-exist")

        shell_text = suite_shell_text(suite)
        markdown = markdown_suite(suite)

        self.assertIn("# P01 base_256p_t2v_smoke: run", shell_text)
        self.assertIn("bash scripts/magihuman_task_runner.sh", shell_text)
        self.assertIn("| P01 | `run` |", markdown)


if __name__ == "__main__":
    unittest.main()
