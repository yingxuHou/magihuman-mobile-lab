import json
import tempfile
import unittest
from pathlib import Path

from backend.experiment_results import build_report, build_summary, feasibility_state, latest_metrics_path
from backend.experiment_matrix import build_matrix


def sample_metrics(width=448, height=256, wall=5.5, vram=40000):
    return {
        "time": {"wall_time_seconds": wall, "max_resident_set_kbytes": 123456},
        "gpu": {"gpu_names": ["NVIDIA H100"], "peak_memory_used_mib": vram, "memory_total_mib": 81559},
        "video": {
            "duration_seconds": 5.0,
            "has_video": True,
            "has_audio": True,
            "width": width,
            "height": height,
            "size_bytes": 1234567,
        },
    }


class ExperimentResultsTest(unittest.TestCase):
    def test_latest_metrics_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = root / "P01_20260101_metrics.json"
            new = root / "P01_20260102_metrics.json"
            old.write_text("{}", encoding="utf-8")
            new.write_text("{}", encoding="utf-8")
            self.assertEqual(latest_metrics_path(root, "P01"), new)

    def test_build_summary_missing(self):
        rows = build_summary(build_matrix(), log_dir="does-not-exist")
        self.assertEqual(rows[0]["status"], "missing_metrics")
        state = feasibility_state(rows)
        self.assertEqual(state["state"], "insufficient_runtime_evidence")
        self.assertIn("P01", state["summary"])

    def test_build_summary_measured(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "P01_test_metrics.json").write_text(json.dumps(sample_metrics()), encoding="utf-8")
            rows = build_summary(build_matrix(), log_dir=root)
            p01 = [row for row in rows if row["id"] == "P01"][0]
            self.assertEqual(p01["status"], "measured")
            self.assertEqual(p01["gpu_names"], "NVIDIA H100")
            self.assertEqual(p01["peak_memory_used_mib"], 40000)

    def test_build_report_markdown(self):
        report = build_report(log_dir="does-not-exist")
        self.assertIn("| P01 | missing_metrics | 256p | t2v |", report["markdown"])
        self.assertEqual(report["state"]["state"], "insufficient_runtime_evidence")


if __name__ == "__main__":
    unittest.main()

