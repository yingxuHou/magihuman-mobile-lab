import tempfile
import unittest

from backend.task_store import TaskStore


class TaskStoreTest(unittest.TestCase):
    def test_create_and_get_t2v_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = TaskStore(tmp)
            task = store.create_task(
                {
                    "prompt": "A presenter says hello.",
                    "language": "en",
                    "resolution": "256p",
                    "mode": "t2v",
                }
            )

            self.assertEqual(task["state"], "queued")
            self.assertEqual(task["resolution"], "256p")
            self.assertEqual(task["mode"], "t2v")
            self.assertIn("magihuman_task_runner.sh", task["worker"]["command_hint"])
            self.assertEqual(store.get_task(task["id"])["prompt"], "A presenter says hello.")

    def test_reject_empty_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = TaskStore(tmp)
            with self.assertRaises(ValueError):
                store.create_task({"prompt": "   "})

    def test_reject_ti2v_without_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = TaskStore(tmp)
            with self.assertRaises(ValueError):
                store.create_task({"prompt": "hello", "mode": "ti2v"})

    def test_update_and_delete_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = TaskStore(tmp)
            task = store.create_task({"prompt": "hello"})
            updated = store.update_task(task["id"], state="running", progress=50)
            self.assertEqual(updated["state"], "running")
            self.assertEqual(updated["progress"], 50)
            self.assertTrue(store.delete_task(task["id"]))
            self.assertIsNone(store.get_task(task["id"]))


if __name__ == "__main__":
    unittest.main()
