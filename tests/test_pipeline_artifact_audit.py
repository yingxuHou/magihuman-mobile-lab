import tempfile
import unittest
from pathlib import Path

from backend.pipeline_artifact_audit import build_artifact_audit, markdown_artifact_audit


def touch(path, text="x"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class PipelineArtifactAuditTest(unittest.TestCase):
    def test_p01_dry_run_artifacts_are_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stamp = "20260716_010203"
            log_dir = root / "logs"
            report_dir = root / "outputs" / "reports"
            for path in [
                log_dir / "p01_preflight_{}.json".format(stamp),
                log_dir / "p01_model_audit_{}.json".format(stamp),
                report_dir / "p01_preflight_{}.md".format(stamp),
                report_dir / "p01_model_audit_{}.md".format(stamp),
                report_dir / "p01_smoke_plan_{}.sh".format(stamp),
                report_dir / "p01_experiment_results_{}.md".format(stamp),
                report_dir / "p01_mobile_video_check_{}.md".format(stamp),
                report_dir / "p01_feasibility_decision_{}.md".format(stamp),
                report_dir / "p01_final_report_{}.md".format(stamp),
            ]:
                touch(path)

            report = build_artifact_audit("p01", stamp, log_dir=log_dir, report_dir=report_dir)

        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["failures"], [])

    def test_missing_report_marks_audit_not_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stamp = "20260716_010203"
            log_dir = root / "logs"
            report_dir = root / "outputs" / "reports"
            touch(log_dir / "p01_preflight_{}.json".format(stamp))
            touch(log_dir / "p01_model_audit_{}.json".format(stamp))

            report = build_artifact_audit("p01", stamp, log_dir=log_dir, report_dir=report_dir)

        self.assertEqual(report["status"], "not_ready")
        self.assertTrue(any(row["label"] == "final report" for row in report["failures"]))

    def test_p01_download_execute_requires_metrics_and_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stamp = "20260716_010203"
            log_dir = root / "logs"
            report_dir = root / "outputs" / "reports"
            result_dir = root / "outputs" / "smoke-test"
            for name in [
                "p01_preflight_{}.json",
                "p01_model_audit_{}.json",
                "p01_hf_access_{}.json",
                "p01_download_models_{}.log",
                "p01_preflight_{}_post_download.json",
                "p01_model_audit_{}_post_download.json",
                "p01_smoke_execute_{}.log",
            ]:
                touch(log_dir / name.format(stamp))
            for name in [
                "p01_preflight_{}.md",
                "p01_model_audit_{}.md",
                "p01_hf_access_{}.md",
                "p01_preflight_{}_post_download.md",
                "p01_model_audit_{}_post_download.md",
                "p01_smoke_plan_{}.sh",
                "p01_experiment_results_{}.md",
                "p01_mobile_video_check_{}.md",
                "p01_feasibility_decision_{}.md",
                "p01_final_report_{}.md",
            ]:
                touch(report_dir / name.format(stamp))
            touch(log_dir / "P01_256p_t2v_20260716_010204_metrics.json")
            touch(result_dir / "P01.mp4")

            report = build_artifact_audit(
                "p01",
                stamp,
                log_dir=log_dir,
                report_dir=report_dir,
                result_dir=result_dir,
                download_models=True,
                execute=True,
            )

        self.assertEqual(report["status"], "ready")

    def test_full_dry_run_requires_dryrun_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stamp = "20260716_010203"
            log_dir = root / "logs"
            report_dir = root / "outputs" / "reports"
            for path in [
                log_dir / "gpu_preflight_{}.json".format(stamp),
                log_dir / "model_audit_{}.json".format(stamp),
                log_dir / "experiment_suite_dryrun_{}.sh".format(stamp),
                report_dir / "gpu_preflight_{}.md".format(stamp),
                report_dir / "model_audit_{}.md".format(stamp),
                report_dir / "experiment_results_{}.md".format(stamp),
                report_dir / "mobile_video_check_{}.md".format(stamp),
                report_dir / "feasibility_decision_{}.md".format(stamp),
                report_dir / "final_report_{}.md".format(stamp),
            ]:
                touch(path)

            report = build_artifact_audit("full", stamp, log_dir=log_dir, report_dir=report_dir)
            text = markdown_artifact_audit(report)

        self.assertEqual(report["status"], "ready")
        self.assertIn("experiment suite dry-run script", text)

    def test_scripts_run_pipeline_artifact_audit(self):
        p01 = Path("scripts/run_p01_smoke_pipeline.sh").read_text(encoding="utf-8")
        full = Path("scripts/gpu_reproduction_pipeline.sh").read_text(encoding="utf-8")
        package = Path("scripts/package_gpu_evidence.sh").read_text(encoding="utf-8")

        self.assertIn("backend.pipeline_artifact_audit --run p01", p01)
        self.assertIn("backend.pipeline_artifact_audit --run full", full)
        self.assertIn("*artifact_audit*.json", package)


if __name__ == "__main__":
    unittest.main()
