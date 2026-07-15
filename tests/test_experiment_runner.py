import json
import tempfile
import unittest
from pathlib import Path

from backend.experiment_matrix import build_matrix
from backend.experiment_runner import case_run_plan, dependency_report, dry_run_text, find_case
from tests.test_experiment_results import sample_metrics


class ExperimentRunnerTest(unittest.TestCase):
    def test_find_case(self):
        case = find_case(build_matrix(), "P01")
        self.assertEqual(case["name"], "base_256p_t2v_smoke")
        with self.assertRaises(ValueError):
            find_case(build_matrix(), "NOPE")

    def test_dependency_report_missing(self):
        matrix = build_matrix()
        case = find_case(matrix, "P04")
        report = dependency_report(case, matrix, log_dir="does-not-exist")
        self.assertFalse(report["ready"])
        self.assertEqual(report["missing"], ["P01", "P03"])

    def test_dependency_report_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "P01_test_metrics.json").write_text(json.dumps(sample_metrics()), encoding="utf-8")
            (root / "P03_test_metrics.json").write_text(json.dumps(sample_metrics()), encoding="utf-8")
            matrix = build_matrix()
            case = find_case(matrix, "P04")
            report = dependency_report(case, matrix, log_dir=root)
            self.assertTrue(report["ready"])
            self.assertEqual(report["missing"], [])

    def test_case_run_plan(self):
        case = find_case(build_matrix(), "T01")
        plan = case_run_plan(case)
        self.assertEqual(plan["command"], "bash scripts/magihuman_task_runner.sh")
        self.assertEqual(plan["env"]["MAGIHUMAN_MODE"], "ti2v")
        self.assertEqual(plan["env"]["MAGIHUMAN_SEED"], "42")
        self.assertIn("MAGIHUMAN_IMAGE_PATH", plan["env"])

    def test_dry_run_text(self):
        case = find_case(build_matrix(), "P01")
        plan = case_run_plan(case)
        text = dry_run_text(plan)
        self.assertIn("export MAGIHUMAN_TASK_ID=P01", text)
        self.assertIn("export MAGIHUMAN_SEED=42", text)
        self.assertIn("bash scripts/magihuman_task_runner.sh", text)


if __name__ == "__main__":
    unittest.main()
