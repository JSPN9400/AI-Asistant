def enqueue_long_running_task(task_name: str, payload: dict) -> dict:
    return {
        "queued": True,
        "task_name": task_name,
        "payload": payload,
    }
