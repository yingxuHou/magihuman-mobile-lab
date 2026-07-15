import argparse
from datetime import timedelta
from pathlib import Path

from backend.task_store import TaskStore, parse_utc, utc_now


def cleanup_expired_results(store, ttl_seconds):
    now = parse_utc(utc_now())
    expired = []
    for task in store.list_tasks():
        result_path = task.get("result_path")
        result_created_at = parse_utc(task.get("result_created_at"))
        if not result_path or not result_created_at:
            continue
        if now - result_created_at < timedelta(seconds=ttl_seconds):
            continue
        path = Path(result_path)
        deleted_file = False
        if path.exists():
            path.unlink()
            deleted_file = True
        updated = store.update_task(
            task["id"],
            result_path=None,
            result_expired_at=utc_now(),
            worker=dict(task.get("worker", {}), result_deleted=deleted_file),
        )
        expired.append(updated)
    return expired


def main():
    parser = argparse.ArgumentParser(description="Clean up expired MagiHuman task results")
    parser.add_argument("--data-dir", default="api_data")
    parser.add_argument("--ttl-seconds", type=int, default=86400)
    args = parser.parse_args()

    store = TaskStore(args.data_dir)
    expired = cleanup_expired_results(store, args.ttl_seconds)
    print("expired_results={}".format(len(expired)))


if __name__ == "__main__":
    main()

