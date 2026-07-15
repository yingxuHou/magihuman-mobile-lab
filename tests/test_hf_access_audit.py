import tempfile
import unittest
import urllib.error
from pathlib import Path

from backend.hf_access_audit import (
    build_access_audit,
    check_probe,
    hf_resolve_url,
    markdown_access_audit,
    resolve_token,
)


class FakeResponse:
    def __init__(self, code=200):
        self.code = code

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def getcode(self):
        return self.code


def ok_opener(request, timeout=20):
    return FakeResponse(200)


def forbidden_opener(request, timeout=20):
    raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", {}, None)


class HuggingFaceAccessAuditTest(unittest.TestCase):
    def test_resolve_token_prefers_env_before_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            token_dir = Path(tmp) / ".cache" / "huggingface"
            token_dir.mkdir(parents=True)
            (token_dir / "token").write_text("cached-token\n", encoding="utf-8")

            token, source = resolve_token(env={"HF_TOKEN": "env-token"}, home=tmp)

        self.assertEqual(token, "env-token")
        self.assertEqual(source, "HF_TOKEN")

    def test_missing_token_blocks_gated_probe_without_network(self):
        probe = {
            "repo_id": "google/t5gemma-9b-9b-ul2",
            "probe_path": "model-00007-of-00009.safetensors",
            "gate": "manual",
        }

        result = check_probe(probe, token=None, opener=forbidden_opener)

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "missing_token")
        self.assertIsNone(result["http_status"])

    def test_access_audit_ready_when_all_probes_are_accessible(self):
        report = build_access_audit(profile="p01", token="secret", opener=ok_opener)

        self.assertEqual(report["status"], "ready")
        self.assertTrue(report["token_present"])
        self.assertEqual(report["token_source"], "argument")
        self.assertEqual(report["failures"], [])

    def test_http_403_marks_report_not_ready(self):
        report = build_access_audit(profile="p01", token="secret", opener=forbidden_opener)

        self.assertEqual(report["status"], "not_ready")
        self.assertEqual(report["failures"][0]["status"], "auth_required_or_forbidden")
        self.assertEqual(report["failures"][0]["http_status"], 403)

    def test_markdown_contains_profile_and_probe_paths(self):
        report = build_access_audit(profile="p01", token="secret", opener=ok_opener)
        text = markdown_access_audit(report)

        self.assertIn("# Hugging Face Access Audit", text)
        self.assertIn("Profile: `p01`", text)
        self.assertIn("base/model-00003-of-00007.safetensors", text)
        self.assertIn("`accessible`", text)

    def test_resolve_url_keeps_repo_namespace_and_quotes_filename(self):
        url = hf_resolve_url("owner/name", "folder/file with space.safetensors")

        self.assertIn("owner/name", url)
        self.assertIn("file%20with%20space.safetensors", url)


if __name__ == "__main__":
    unittest.main()
