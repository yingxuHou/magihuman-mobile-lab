import json
import subprocess
import unittest
from pathlib import Path

from backend.upstream_drift_audit import (
    build_upstream_drift_audit,
    check_git_source,
    check_hf_source,
    markdown_upstream_drift_audit,
)


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.data).encode("utf-8")


def fake_runner(command, capture_output=True, text=True, timeout=30):
    return subprocess.CompletedProcess(command, 0, stdout="abc123\trefs/heads/main\n", stderr="")


def failing_runner(command, capture_output=True, text=True, timeout=30):
    return subprocess.CompletedProcess(command, 128, stdout="", stderr="network failed")


def fake_opener(url, timeout=30):
    return FakeResponse({"sha": "abc123", "lastModified": "2026-07-16T00:00:00.000Z"})


class UpstreamDriftAuditTest(unittest.TestCase):
    def test_git_source_matches_lock(self):
        source = {
            "id": "repo",
            "kind": "git",
            "source": "https://example.com/repo.git",
            "ref": "refs/heads/main",
            "locked_sha": "abc123",
        }

        row = check_git_source(source, runner=fake_runner)

        self.assertEqual(row["status"], "matches_lock")
        self.assertEqual(row["upstream_sha"], "abc123")

    def test_hf_source_detects_drift(self):
        source = {
            "id": "model",
            "kind": "hf_model",
            "source": "owner/model",
            "api_url": "https://example.com/api/models/owner/model",
            "locked_sha": "locked",
        }

        row = check_hf_source(source, opener=fake_opener)

        self.assertEqual(row["status"], "upstream_moved")
        self.assertEqual(row["upstream_sha"], "abc123")

    def test_audit_status_incomplete_when_source_unreachable(self):
        source = {
            "id": "repo",
            "kind": "git",
            "source": "https://example.com/repo.git",
            "ref": "refs/heads/main",
            "locked_sha": "abc123",
        }

        report = build_upstream_drift_audit(sources=[source], runner=failing_runner)

        self.assertEqual(report["status"], "incomplete")
        self.assertEqual(report["unreachable"][0]["detail"], "network failed")

    def test_markdown_contains_status_and_rows(self):
        source = {
            "id": "repo",
            "kind": "git",
            "source": "https://example.com/repo.git",
            "ref": "refs/heads/main",
            "locked_sha": "abc123",
        }
        report = build_upstream_drift_audit(sources=[source], runner=fake_runner)
        text = markdown_upstream_drift_audit(report)

        self.assertIn("# Upstream Drift Audit", text)
        self.assertIn("`locked_current`", text)
        self.assertIn("repo", text)

    def test_bootstrap_script_generates_upstream_drift_report(self):
        text = Path("scripts/bootstrap_gpu_host.sh").read_text(encoding="utf-8")

        self.assertIn("backend.upstream_drift_audit", text)
        self.assertIn("upstream_drift_audit.md", text)


if __name__ == "__main__":
    unittest.main()
