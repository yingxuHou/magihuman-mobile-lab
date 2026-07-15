import json
import tempfile
import unittest
from pathlib import Path

from backend.experiment_matrix import build_matrix
from backend.metrics_context_audit import build_metrics_context_audit, markdown_metrics_context_audit
from backend.run_metrics import sha256_file, sha256_text
from tests.test_feasibility_decision import sample_metrics


def find_case(case_id):
    for case in build_matrix():
        if case["id"] == case_id:
            return case
    raise ValueError(case_id)


def write_p01_manifest(root):
    case = find_case("P01")
    manifest = {
        "actual_p01_inputs": {
            "case_id": "P01",
            "mode": "t2v",
            "resolution": "256p",
            "variant": "base",
            "duration_seconds": case["duration_seconds"],
            "seed": case["seed"],
            "prompt_sha256": sha256_text(case["prompt"]),
            "base_width": case["profile"]["br_width"],
            "base_height": case["profile"]["br_height"],
            "sr_width": None,
            "sr_height": None,
            "expected_result_path": "outputs/smoke-test/P01.mp4",
        }
    }
    path = root / "p01-smoke-manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def matching_run_context(case, manifest_path=None, seed=None):
    profile = case["profile"]
    context = {
        "case_id": case["id"],
        "mode": case["mode"],
        "resolution": case["resolution"],
        "variant": case["variant"],
        "seed": seed if seed is not None else case["seed"],
        "target_duration_seconds": float(case["duration_seconds"]),
        "target_br_width": profile["br_width"],
        "target_br_height": profile["br_height"],
        "result_path": "outputs/experiment-results/{}.mp4".format(case["id"]),
        "prompt_sha256": sha256_text(case["prompt"]),
    }
    if case["id"] == "P01" and manifest_path:
        context["result_path"] = "outputs/smoke-test/P01.mp4"
        context["manifest_path"] = str(manifest_path).replace("\\", "/")
        context["manifest_sha256"] = sha256_file(manifest_path)
    return context


def write_metrics(root, case_id, run_context=None):
    payload = sample_metrics()
    if run_context is not None:
        payload["run"] = run_context
    path = root / "{}_test_metrics.json".format(case_id)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class MetricsContextAuditTest(unittest.TestCase):
    def test_matching_p01_context_is_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = write_p01_manifest(root)
            case = find_case("P01")
            write_metrics(root, "P01", matching_run_context(case, manifest_path=manifest))

            audit = build_metrics_context_audit(log_dir=root, p01_manifest_path=manifest)

        p01 = [row for row in audit["rows"] if row["case_id"] == "P01"][0]
        self.assertEqual(audit["status"], "context_ready")
        self.assertEqual(p01["status"], "context_ready")

    def test_missing_run_context_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = write_p01_manifest(root)
            write_metrics(root, "P01")

            audit = build_metrics_context_audit(log_dir=root, p01_manifest_path=manifest)

        p01 = [row for row in audit["rows"] if row["case_id"] == "P01"][0]
        self.assertEqual(audit["status"], "context_not_ready")
        self.assertEqual(p01["status"], "missing_run_context")

    def test_seed_mismatch_fails_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = write_p01_manifest(root)
            case = find_case("P01")
            write_metrics(root, "P01", matching_run_context(case, manifest_path=manifest, seed=7))

            audit = build_metrics_context_audit(log_dir=root, p01_manifest_path=manifest)

        p01 = [row for row in audit["rows"] if row["case_id"] == "P01"][0]
        failed = {check["field"] for check in p01["failed_checks"]}
        self.assertEqual(p01["status"], "context_mismatch")
        self.assertIn("seed", failed)
        self.assertIn("manifest_seed", failed)

    def test_markdown_lists_failed_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = write_p01_manifest(root)
            write_metrics(root, "P01")
            text = markdown_metrics_context_audit(build_metrics_context_audit(log_dir=root, p01_manifest_path=manifest))

        self.assertIn("# Metrics Context Audit", text)
        self.assertIn("missing_run_context", text)


if __name__ == "__main__":
    unittest.main()
