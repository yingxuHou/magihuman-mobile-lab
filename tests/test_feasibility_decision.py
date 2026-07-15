import json
import tempfile
import unittest
from pathlib import Path

from backend.feasibility_decision import build_decision, markdown_decision
from backend.quality_review import build_review_template


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


def write_required_metrics(root):
    for case_id in ["P01", "P03", "P04", "T01", "T02"]:
        (root / "{}_test_metrics.json".format(case_id)).write_text(json.dumps(sample_metrics()), encoding="utf-8")


def write_quality_review(root, passing=True):
    review = build_review_template()
    for item in review["case_reviews"]:
        item["playable_on_phone"] = True
        item["audio_video_sync_score"] = 4
        item["face_quality_score"] = 4 if passing else 2
        item["motion_naturalness_score"] = 3
        item["speech_intelligibility_score"] = 4
        item["artifact_free_score"] = 3
    path = root / "quality_review.json"
    path.write_text(json.dumps(review), encoding="utf-8")
    return path


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
            write_required_metrics(root)

            decision = build_decision(log_dir=root)

        self.assertEqual(decision["recommendation"], "B_candidate_needs_quality_review")
        self.assertEqual(decision["decisions"]["official_on_device"]["status"], "not_viable")
        self.assertEqual(decision["decisions"]["cloud_backend"]["status"], "measured_needs_quality_review")
        self.assertEqual(decision["runtime_evidence"]["missing_required_case_ids"], [])
        self.assertEqual(decision["quality_evidence"]["status"], "missing_quality_review")

    def test_quality_review_passed_moves_cloud_to_cost_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_required_metrics(root)
            quality_path = write_quality_review(root, passing=True)

            decision = build_decision(log_dir=root, quality_review_path=quality_path)

        self.assertEqual(decision["recommendation"], "B_candidate_needs_cost_review")
        self.assertEqual(decision["decisions"]["cloud_backend"]["status"], "quality_passed_needs_cost_review")

    def test_failed_quality_review_recommends_stop_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_required_metrics(root)
            quality_path = write_quality_review(root, passing=False)

            decision = build_decision(log_dir=root, quality_review_path=quality_path)

        self.assertEqual(decision["recommendation"], "C_candidate_quality_failed")
        self.assertEqual(decision["decisions"]["cloud_backend"]["status"], "quality_review_failed")

    def test_markdown_decision_contains_key_result(self):
        text = markdown_decision(build_decision(log_dir="does-not-exist"))

        self.assertIn("Official on-device inference", text)
        self.assertIn("`B_pending_runtime`", text)
        self.assertIn("285.63 GiB", text)
        self.assertIn("P01, P03, P04, T01, T02", text)
        self.assertIn("Quality Evidence", text)


if __name__ == "__main__":
    unittest.main()
