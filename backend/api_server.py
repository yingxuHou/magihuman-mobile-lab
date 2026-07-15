import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from backend.task_store import TaskStore


class ApiHandler(BaseHTTPRequestHandler):
    store = None

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self._json(200, {"status": "ok"})
            return
        if path == "/tasks":
            self._json(200, {"tasks": self.store.list_tasks()})
            return

        parts = self._parts(path)
        if len(parts) == 2 and parts[0] == "tasks":
            task = self.store.get_task(parts[1])
            if not task:
                self._json(404, {"error": "task not found"})
                return
            self._json(200, task)
            return

        if len(parts) == 3 and parts[0] == "tasks" and parts[2] == "result":
            self._send_result(parts[1])
            return

        self._json(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/tasks":
            self._json(404, {"error": "not found"})
            return
        try:
            payload = self._read_json()
            task = self.store.create_task(payload)
        except ValueError as exc:
            self._json(400, {"error": str(exc)})
            return
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid json"})
            return
        self._json(202, task)

    def do_DELETE(self):
        parts = self._parts(urlparse(self.path).path)
        if len(parts) != 2 or parts[0] != "tasks":
            self._json(404, {"error": "not found"})
            return
        deleted = self.store.delete_task(parts[1])
        if not deleted:
            self._json(404, {"error": "task not found"})
            return
        self._json(200, {"deleted": True, "id": parts[1]})

    def log_message(self, fmt, *args):
        return

    def _send_result(self, task_id):
        task = self.store.get_task(task_id)
        if not task:
            self._json(404, {"error": "task not found"})
            return
        result_path = task.get("result_path")
        if not result_path:
            self._json(404, {"error": "result not ready"})
            return
        path = Path(result_path)
        if not path.exists():
            self._json(404, {"error": "result file missing"})
            return

        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(path.stat().st_size))
        self.end_headers()
        with path.open("rb") as f:
            self.wfile.write(f.read())

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        if not body:
            return {}
        return json.loads(body)

    def _json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _parts(self, path):
        return [part for part in path.strip("/").split("/") if part]


def build_server(host, port, data_dir):
    ApiHandler.store = TaskStore(data_dir)
    return ThreadingHTTPServer((host, port), ApiHandler)


def main():
    parser = argparse.ArgumentParser(description="MagiHuman Mobile Lab API prototype")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--data-dir", default="api_data")
    args = parser.parse_args()

    server = build_server(args.host, args.port, args.data_dir)
    print("Serving on http://{}:{}".format(args.host, args.port))
    server.serve_forever()


if __name__ == "__main__":
    main()

