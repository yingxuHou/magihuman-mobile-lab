import argparse
import os
import shlex
import subprocess
from pathlib import Path

from backend.task_store import TaskStore, utc_now


def next_queued_task(store):
    tasks = [task for task in store.list_tasks() if task["state"] == "queued"]
    if not tasks:
        return None
    return sorted(tasks, key=lambda task: task["created_at"])[0]


def render_command(command_template, task, result_path):
    return command_template.format(
        task_id=task["id"],
        mode=task["mode"],
        resolution=task["resolution"],
        result_path=str(result_path),
    )


def process_next_task(store, command_template, output_dir, timeout_seconds=3600):
    task = next_queued_task(store)
    if not task:
        return None

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "{}.mp4".format(task["id"])
    command = render_command(command_template, task, result_path)

    store.update_task(
        task["id"],
        state="running",
        progress=1,
        error=None,
        worker={
            "required": "gpu",
            "status": "running",
            "command": command,
            "started_at": utc_now(),
        },
    )

    env = os.environ.copy()
    env.update(
        {
            "MAGIHUMAN_TASK_ID": task["id"],
            "MAGIHUMAN_PROMPT": task["prompt"],
            "MAGIHUMAN_LANGUAGE": task["language"],
            "MAGIHUMAN_MODE": task["mode"],
            "MAGIHUMAN_RESOLUTION": task["resolution"],
            "MAGIHUMAN_DURATION_SECONDS": str(task["duration_seconds"]),
            "MAGIHUMAN_RESULT_PATH": str(result_path),
            "MAGIHUMAN_IMAGE_PATH": task.get("image_path") or "",
            "MAGIHUMAN_AUDIO_PATH": task.get("audio_path") or "",
        }
    )

    try:
        completed = subprocess.run(
            command,
            shell=True,
            cwd=str(Path.cwd()),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return fail_or_retry_task(
            store,
            task,
            error="worker timeout after {} seconds".format(timeout_seconds),
            worker_status="timeout",
            command=command,
            stdout="",
            stderr=str(exc),
        )

    if completed.returncode != 0:
        return fail_or_retry_task(
            store,
            task,
            error="worker exited with code {}".format(completed.returncode),
            worker_status="failed",
            command=command,
            stdout=completed.stdout[-4000:],
            stderr=completed.stderr[-4000:],
        )

    if not result_path.exists():
        return fail_or_retry_task(
            store,
            task,
            error="worker completed but result file was not created",
            worker_status="missing_result",
            command=command,
            stdout=completed.stdout[-4000:],
            stderr=completed.stderr[-4000:],
        )

    return store.update_task(
        task["id"],
        state="succeeded",
        progress=100,
        error=None,
        result_path=str(result_path),
        result_created_at=utc_now(),
        result_expired_at=None,
        worker={
            "required": "gpu",
            "status": "succeeded",
            "command": command,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
            "finished_at": utc_now(),
        },
    )


def fail_or_retry_task(store, task, error, worker_status, command, stdout="", stderr=""):
    retry_count = int(task.get("retry_count", 0))
    max_retries = int(task.get("max_retries", 0))
    next_retry_count = retry_count + 1
    if retry_count < max_retries:
        return store.update_task(
            task["id"],
            state="queued",
            progress=0,
            retry_count=next_retry_count,
            error=error,
            worker={
                "required": "gpu",
                "status": "retry_queued",
                "previous_status": worker_status,
                "command": command,
                "stdout": stdout,
                "stderr": stderr,
                "finished_at": utc_now(),
                "retry_count": next_retry_count,
                "max_retries": max_retries,
            },
        )

    return store.update_task(
        task["id"],
        state="failed",
        progress=100,
        retry_count=next_retry_count,
        error=error,
        worker={
            "required": "gpu",
            "status": worker_status,
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "finished_at": utc_now(),
            "retry_count": next_retry_count,
            "max_retries": max_retries,
        },
    )


def shell_quote(value):
    return shlex.quote(str(value))


def main():
    parser = argparse.ArgumentParser(description="MagiHuman GPU worker prototype")
    parser.add_argument("--data-dir", default="api_data")
    parser.add_argument("--output-dir", default="outputs/api-results")
    parser.add_argument("--command", required=True, help="Command template executed for one queued task.")
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    args = parser.parse_args()

    store = TaskStore(args.data_dir)
    task = process_next_task(store, args.command, args.output_dir, args.timeout_seconds)
    if not task:
        print("No queued task.")
        return
    print("{} {}".format(task["id"], task["state"]))


if __name__ == "__main__":
    main()
