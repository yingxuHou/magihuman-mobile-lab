import tempfile
import unittest
from pathlib import Path

from backend.gpu_execution_packet import (
    DEFAULT_REPO_URL,
    build_execution_packet,
    build_fresh_host_commands,
    build_local_budget_commands,
    build_local_import_commands,
    markdown_execution_packet,
)


class GpuExecutionPacketTest(unittest.TestCase):
    def test_current_project_packet_requires_budget_guard(self):
        packet = build_execution_packet(project_root=".", repo_url=DEFAULT_REPO_URL)

        self.assertEqual(packet["status"], "attention_required")
        self.assertEqual(packet["local_runtime_status"], "not_executed_on_this_workstation")
        self.assertEqual(packet["gpu_session_budget"]["status"], "incomplete_budget_config")
        self.assertTrue(any(item["label"] == "GPU session budget guard" for item in packet["failures"]))
        self.assertTrue(any(item == "outputs/gpu-evidence-*.tar.gz" for item in packet["expected_artifacts"]))

    def test_missing_project_artifacts_need_attention(self):
        with tempfile.TemporaryDirectory() as tmp:
            packet = build_execution_packet(project_root=tmp, repo_url="https://example.test/repo.git")

        self.assertEqual(packet["status"], "attention_required")
        self.assertTrue(any(item["label"] == "P01 smoke manifest exists" for item in packet["failures"]))
        self.assertTrue(any(item["label"] == "workflow readiness" for item in packet["failures"]))

    def test_fresh_host_commands_clone_checkout_and_bootstrap(self):
        commands = build_fresh_host_commands("https://example.test/repo.git", branch="main")

        self.assertEqual(commands[0], "git clone https://example.test/repo.git")
        self.assertIn("git checkout main", commands)
        self.assertIn("export HF_TOKEN=<your_huggingface_token>", commands)
        self.assertIn("bash scripts/bootstrap_gpu_host.sh", commands)

    def test_packet_container_command_uses_gpu_workflow(self):
        packet = build_execution_packet(project_root=".", repo_url=DEFAULT_REPO_URL)
        container_text = "\n".join(packet["container_commands"])

        self.assertIn("bash scripts/run_gpu_reproduction_workflow.sh", container_text)
        self.assertIn("P01_DOWNLOAD_MODELS=1", container_text)
        self.assertIn("FULL_DOWNLOAD_MODELS=1", container_text)

    def test_local_import_commands_keep_reviews_and_final_report(self):
        commands = "\n".join(build_local_import_commands())

        self.assertIn("import_gpu_evidence_package.ps1", commands)
        self.assertIn("backend.review_readiness", commands)
        self.assertIn("backend.final_report", commands)

    def test_local_budget_commands_include_strict_guard(self):
        commands = "\n".join(build_local_budget_commands())

        self.assertIn("backend.gpu_session_budget", commands)
        self.assertIn("--strict", commands)
        self.assertIn("docs\\gpu-session-budget.json", commands)

    def test_markdown_packet_contains_operator_sections(self):
        text = markdown_execution_packet(build_execution_packet(project_root=".", repo_url=DEFAULT_REPO_URL))

        self.assertIn("# GPU Execution Packet", text)
        self.assertIn("GPU session budget", text)
        self.assertIn("## Budget Guard Status", text)
        self.assertIn("## Local Budget Guard", text)
        self.assertIn("## Fresh GPU Host Commands", text)
        self.assertIn("## Return Evidence", text)
        self.assertIn("Do not change the final mobile App recommendation", text)

    def test_wrapper_scripts_call_packet_module(self):
        bash_text = Path("scripts/generate_gpu_execution_packet.sh").read_text(encoding="utf-8")
        ps1_text = Path("scripts/generate_gpu_execution_packet.ps1").read_text(encoding="utf-8")

        self.assertIn("backend.gpu_execution_packet", bash_text)
        self.assertIn("backend.gpu_execution_packet", ps1_text)


if __name__ == "__main__":
    unittest.main()
