import unittest
from pathlib import Path


class PipelineScriptTest(unittest.TestCase):
    def read_script(self, path):
        return Path(path).read_text(encoding="utf-8")

    def test_p01_download_flow_does_not_strict_audit_before_download(self):
        text = self.read_script("scripts/run_p01_smoke_pipeline.sh")

        self.assertIn('INITIAL_MODEL_AUDIT_STRICT=0', text)
        self.assertIn('if [ "${EXECUTE}" = "1" ] && [ "${DOWNLOAD_MODELS}" != "1" ]; then', text)
        self.assertIn('run_model_audit "${STAMP}" "${INITIAL_MODEL_AUDIT_STRICT}"', text)
        self.assertIn("backend.hf_access_audit --profile p01", text)
        self.assertIn("backend.download_log_audit", text)
        self.assertIn('if [ "${DOWNLOAD_MODELS}" = "1" ] && [ "${HF_ACCESS_AUDIT}" = "1" ]; then', text)
        self.assertIn('DOWNLOAD_PROFILE="${MODEL_PROFILE:-p01}"', text)
        self.assertIn('MODEL_PROFILE="${DOWNLOAD_PROFILE}"', text)
        self.assertIn('run_model_audit "${STAMP}_post_download" "1"', text)

    def test_full_pipeline_download_flow_does_not_strict_audit_before_download(self):
        text = self.read_script("scripts/gpu_reproduction_pipeline.sh")

        self.assertIn('INITIAL_MODEL_AUDIT_STRICT=0', text)
        self.assertIn('if [ "${EXECUTE}" = "1" ] && [ "${DOWNLOAD_MODELS}" != "1" ]; then', text)
        self.assertIn('run_model_audit "${STAMP}" "${INITIAL_MODEL_AUDIT_STRICT}"', text)
        self.assertIn("backend.hf_access_audit --profile required_suite", text)
        self.assertIn("backend.download_log_audit", text)
        self.assertIn("backend.required_suite_acceptance", text)
        self.assertIn("backend.review_readiness", text)
        self.assertIn('if [ "${DOWNLOAD_MODELS}" = "1" ] && [ "${HF_ACCESS_AUDIT}" = "1" ]; then', text)
        self.assertIn('DOWNLOAD_PROFILE="${MODEL_PROFILE:-required_suite}"', text)
        self.assertIn('MODEL_PROFILE="${DOWNLOAD_PROFILE}"', text)
        self.assertIn('run_model_audit "${STAMP}_post_download" "1"', text)

    def test_preflight_still_strict_when_downloading_models(self):
        text = self.read_script("scripts/run_p01_smoke_pipeline.sh")

        self.assertIn('if [ "${EXECUTE}" = "1" ] || [ "${DOWNLOAD_MODELS}" = "1" ]; then', text)
        self.assertIn('run_preflight "${STAMP}" "${INITIAL_REQUIRE_MODELS}" "${INITIAL_STRICT}"', text)


if __name__ == "__main__":
    unittest.main()
