import http.client
import json
import tempfile
import threading
import unittest

from backend.api_server import build_server


class ApiServerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.server = build_server("127.0.0.1", 0, self.tmp.name)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        self.host, self.port = self.server.server_address

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()
        self.tmp.cleanup()

    def request(self, method, path, payload=None):
        conn = http.client.HTTPConnection(self.host, self.port, timeout=5)
        body = None
        headers = {}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        parsed = json.loads(data.decode("utf-8")) if data else None
        return response.status, parsed

    def test_health(self):
        status, payload = self.request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")

    def test_create_get_delete_task(self):
        status, task = self.request(
            "POST",
            "/tasks",
            {"prompt": "A presenter says hello.", "resolution": "256p", "mode": "t2v"},
        )
        self.assertEqual(status, 202)
        task_id = task["id"]

        status, fetched = self.request("GET", "/tasks/{}".format(task_id))
        self.assertEqual(status, 200)
        self.assertEqual(fetched["id"], task_id)

        status, result = self.request("GET", "/tasks/{}/result".format(task_id))
        self.assertEqual(status, 404)
        self.assertEqual(result["error"], "result not ready")

        status, deleted = self.request("DELETE", "/tasks/{}".format(task_id))
        self.assertEqual(status, 200)
        self.assertTrue(deleted["deleted"])


if __name__ == "__main__":
    unittest.main()
