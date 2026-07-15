import unittest

from backend.gpu_bootstrap import (
    DEFAULT_DOCKER_IMAGE,
    MAGIHUMAN_COMMIT,
    build_bootstrap_plan,
    container_commands,
    docker_run_command,
    markdown_plan,
    shell_plan,
)


class GpuBootstrapTest(unittest.TestCase):
    def test_docker_run_command_mounts_project_root(self):
        command = docker_run_command(project_root="/work/magihuman")

        self.assertIn("--gpus all", command)
        self.assertIn("-e HF_TOKEN", command)
        self.assertIn("-e HUGGINGFACE_HUB_TOKEN", command)
        self.assertIn('-v "/work/magihuman:/repo"', command)
        self.assertIn(DEFAULT_DOCKER_IMAGE, command)

    def test_container_commands_include_pipeline_flags(self):
        commands = container_commands(download_models=True, execute=True, include_optional=True)

        self.assertIn("INSTALL_MAGICOMPILER=1 bash scripts/prepare_sources.sh", commands)
        self.assertIn(
            "PREPARE_SOURCES=0 DOWNLOAD_MODELS=1 EXECUTE=1 INCLUDE_OPTIONAL=1 bash scripts/gpu_reproduction_pipeline.sh",
            commands,
        )

    def test_bootstrap_plan_contains_verified_commits(self):
        plan = build_bootstrap_plan()

        self.assertEqual(plan["verified_sources"]["daVinci-MagiHuman"]["commit"], MAGIHUMAN_COMMIT)
        self.assertIn("docker pull {}".format(DEFAULT_DOCKER_IMAGE), plan["host_commands"])

    def test_markdown_plan_contains_sections(self):
        text = markdown_plan(build_bootstrap_plan())

        self.assertIn("# GPU Bootstrap Plan", text)
        self.assertIn("## Verified Sources", text)
        self.assertIn(MAGIHUMAN_COMMIT, text)

    def test_shell_plan_contains_docker_run(self):
        text = shell_plan(build_bootstrap_plan())

        self.assertIn("#!/usr/bin/env bash", text)
        self.assertIn("docker run --rm -it", text)


if __name__ == "__main__":
    unittest.main()
