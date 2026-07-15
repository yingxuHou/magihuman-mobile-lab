import json
import uuid
from datetime import datetime
from pathlib import Path


VALID_STATES = {"queued", "running", "succeeded", "failed", "canceled"}
VALID_RESOLUTIONS = {"256p", "540p", "1080p"}
VALID_MODES = {"t2v", "ti2v"}


def utc_now():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class TaskStore:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "tasks.json"
        self.tasks_dir = self.root / "tasks"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        if not self.db_path.exists():
            self._write({})

    def create_task(self, payload):
        prompt = str(payload.get("prompt", "")).strip()
        if not prompt:
            raise ValueError("prompt is required")

        resolution = str(payload.get("resolution", "256p"))
        if resolution not in VALID_RESOLUTIONS:
            raise ValueError("resolution must be one of: 256p, 540p, 1080p")

        mode = str(payload.get("mode", "t2v"))
        if mode not in VALID_MODES:
            raise ValueError("mode must be one of: t2v, ti2v")

        if mode == "ti2v" and not str(payload.get("image_path", "")).strip():
            raise ValueError("image_path is required for ti2v mode")

        task_id = uuid.uuid4().hex
        now = utc_now()
        task = {
            "id": task_id,
            "state": "queued",
            "created_at": now,
            "updated_at": now,
            "prompt": prompt,
            "language": str(payload.get("language", "auto")),
            "mode": mode,
            "resolution": resolution,
            "duration_seconds": int(payload.get("duration_seconds", 5)),
            "image_path": payload.get("image_path"),
            "audio_path": payload.get("audio_path"),
            "priority": int(payload.get("priority", 0)),
            "progress": 0,
            "error": None,
            "result_path": None,
            "worker": {
                "required": "gpu",
                "status": "not_started",
                "command_hint": self._command_hint(mode, resolution),
            },
        }
        data = self._read()
        data[task_id] = task
        self._write(data)
        return task

    def list_tasks(self):
        data = self._read()
        return sorted(data.values(), key=lambda item: item["created_at"], reverse=True)

    def get_task(self, task_id):
        return self._read().get(task_id)

    def update_task(self, task_id, **updates):
        data = self._read()
        if task_id not in data:
            return None
        task = data[task_id]
        if "state" in updates and updates["state"] not in VALID_STATES:
            raise ValueError("invalid task state")
        for key, value in updates.items():
            task[key] = value
        task["updated_at"] = utc_now()
        data[task_id] = task
        self._write(data)
        return task

    def delete_task(self, task_id):
        data = self._read()
        if task_id not in data:
            return False
        del data[task_id]
        self._write(data)
        return True

    def _command_hint(self, mode, resolution):
        if resolution == "256p" and mode == "t2v":
            return "MODEL_ROOT=models bash scripts/run_base_t2v_smoke.sh"
        if resolution == "256p" and mode == "ti2v":
            return "Run official example/base/run_TI2V.sh on the GPU host"
        if resolution == "540p":
            return "Run official example/sr_540p script on the GPU host after 256p passes"
        return "Run official example/sr_1080p script on the GPU host after 256p and 540p pass"

    def _read(self):
        if not self.db_path.exists():
            return {}
        with self.db_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        tmp_path = self.db_path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        tmp_path.replace(self.db_path)

