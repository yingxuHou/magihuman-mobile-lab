import tempfile
import unittest
from pathlib import Path

from backend.retention import cleanup_expired_results
from backend.task_store import TaskStore


class RetentionTest(unittest.TestCase):
    def test_cleanup_expired_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = root / "result.mp4"
            result.write_text("video", encoding="utf-8")

            store = TaskStore(root / "api")
            task = store.create_task({"prompt": "hello"})
            store.update_task(
                task["id"],
                state="succeeded",
                result_path=str(result),
                result_created_at="2000-01-01T00:00:00Z",
            )

            expired = cleanup_expired_results(store, ttl_seconds=1)
            updated = store.get_task(task["id"])

            self.assertEqual(len(expired), 1)
            self.assertFalse(result.exists())
            self.assertIsNone(updated["result_path"])
            self.assertIsNotNone(updated["result_expired_at"])

    def test_cleanup_keeps_recent_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = root / "result.mp4"
            result.write_text("video", encoding="utf-8")

            store = TaskStore(root / "api")
            task = store.create_task({"prompt": "hello"})
            store.update_task(
                task["id"],
                state="succeeded",
                result_path=str(result),
                result_created_at="2999-01-01T00:00:00Z",
            )

            expired = cleanup_expired_results(store, ttl_seconds=1)

            self.assertEqual(expired, [])
            self.assertTrue(result.exists())


if __name__ == "__main__":
    unittest.main()

