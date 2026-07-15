import sys
import tempfile
import unittest
from pathlib import Path

from backend.task_store import TaskStore
from backend.worker import process_next_task


class WorkerTest(unittest.TestCase):
    def test_process_successful_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "mock_success.py"
            script.write_text(
                "import os\n"
                "from pathlib import Path\n"
                "Path(os.environ['MAGIHUMAN_RESULT_PATH']).write_text('mock video')\n",
                encoding="utf-8",
            )

            store = TaskStore(root / "api")
            task = store.create_task({"prompt": "hello", "resolution": "256p", "mode": "t2v"})
            command = '"{}" "{}"'.format(sys.executable, script)

            updated = process_next_task(store, command, root / "outputs", timeout_seconds=10)

            self.assertEqual(updated["id"], task["id"])
            self.assertEqual(updated["state"], "succeeded")
            self.assertEqual(updated["progress"], 100)
            self.assertTrue(Path(updated["result_path"]).exists())

    def test_process_failed_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "mock_fail.py"
            script.write_text("import sys\nsys.exit(7)\n", encoding="utf-8")

            store = TaskStore(root / "api")
            task = store.create_task({"prompt": "hello", "resolution": "256p", "mode": "t2v"})
            command = '"{}" "{}"'.format(sys.executable, script)

            updated = process_next_task(store, command, root / "outputs", timeout_seconds=10)

            self.assertEqual(updated["id"], task["id"])
            self.assertEqual(updated["state"], "failed")
            self.assertIn("worker exited with code 7", updated["error"])

    def test_process_failed_task_with_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "mock_fail.py"
            script.write_text("import sys\nsys.exit(7)\n", encoding="utf-8")

            store = TaskStore(root / "api")
            task = store.create_task({"prompt": "hello", "resolution": "256p", "mode": "t2v", "max_retries": 1})
            command = '"{}" "{}"'.format(sys.executable, script)

            first = process_next_task(store, command, root / "outputs", timeout_seconds=10)
            self.assertEqual(first["id"], task["id"])
            self.assertEqual(first["state"], "queued")
            self.assertEqual(first["retry_count"], 1)
            self.assertEqual(first["worker"]["status"], "retry_queued")

            second = process_next_task(store, command, root / "outputs", timeout_seconds=10)
            self.assertEqual(second["state"], "failed")
            self.assertEqual(second["retry_count"], 2)

    def test_no_queued_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = TaskStore(root / "api")
            result = process_next_task(store, "unused", root / "outputs", timeout_seconds=10)
            self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
