import tempfile
import unittest
from pathlib import Path

from backend.experiment_matrix import build_matrix, markdown_table, write_matrix


class ExperimentMatrixTest(unittest.TestCase):
    def test_build_matrix_contains_required_cases(self):
        matrix = build_matrix()
        ids = {case["id"] for case in matrix}
        self.assertTrue({"P01", "P03", "P04", "T01", "T02"}.issubset(ids))
        self.assertEqual(len(matrix), 8)
        self.assertTrue(all(case["seed"] == 42 for case in matrix))

    def test_runner_env_for_ti2v_has_image_path(self):
        case = [item for item in build_matrix() if item["id"] == "T01"][0]
        self.assertEqual(case["runner_env"]["MAGIHUMAN_MODE"], "ti2v")
        self.assertEqual(case["runner_env"]["MAGIHUMAN_SEED"], "42")
        self.assertIn("MAGIHUMAN_IMAGE_PATH", case["runner_env"])

    def test_1080p_profile(self):
        case = [item for item in build_matrix() if item["id"] == "P04"][0]
        self.assertEqual(case["profile"]["sr_width"], 1920)
        self.assertEqual(case["profile"]["sr_height"], 1088)
        self.assertEqual(case["profile"]["config_template"], "example/sr_1080p/config.json")

    def test_write_matrix(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "matrix.json"
            matrix = write_matrix(path)
            self.assertTrue(path.exists())
            self.assertEqual(len(matrix), 8)

    def test_markdown_table(self):
        table = markdown_table(build_matrix())
        self.assertIn("| P01 | performance | en | t2v | 256p | base | yes | - |", table)
        self.assertIn("| T01 | multilingual | zh | ti2v | 256p | base | yes | P01 |", table)


if __name__ == "__main__":
    unittest.main()
