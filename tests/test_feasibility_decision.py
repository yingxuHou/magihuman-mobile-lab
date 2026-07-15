import json
import tempfile
import unittest
from pathlib import Path

from backend.feasibility_decision import build_decision, markdown_decision


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


class FeasibilityDecisionTest(unittest.TestCase):
    def test_missing_metrics_rejects_official_on_device_and_keeps_cloud_pending(self):
        decision = build_decision(log_dir="does-not-exist")

        self.assertEqual(decision["recommendation"], "B_pending_runtime")
        self.assertEqual(decision["decisions"]["official_on_device"]["status"], "not_viable")
        self.assertEqual(decision["decisions"]["cloud_backend"]["status"], "pending_runtime_evidence")
        self.assertEqual(
            decision["runtime_evidence"]["missing_required_case_ids"],
            ["P01", "P03", "P04", "T01", "T02"],
        )

    def test_measured_required_cases_move_cloud_to_quality_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for case_id in ["P01", "P03", "P04", "T01", "T02"]:
                (root / "{}_test_metrics.json".format(case_id)).write_text(
                    json.dumps(sample_metrics()), encoding="utf-8"
                )

            decision = build_decision(log_dir=root)

        self.assertEqual(decision["recommendation"], "B_candidate_needs_quality_review")
        self.assertEqual(decision["decisions"]["official_on_device"]["status"], "not_viable")
        self.assertEqual(decision["decisions"]["cloud_backend"]["status"], "measured_needs_quality_review")
        self.assertEqual(decision["runtime_evidence"]["missing_required_case_ids"], [])

    def test_markdown_decision_contains_key_result(self):
        text = markdown_decision(build_decision(log_dir="does-not-exist"))

        self.assertIn("Official on-device inference", text)
        self.assertIn("`B_pending_runtime`", text)
        self.assertIn("285.63 GiB", text)
        self.assertIn("P01, P03, P04, T01, T02", text)


if __name__ == "__main__":
    unittest.main()
