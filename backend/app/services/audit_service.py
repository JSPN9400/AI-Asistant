import logging


logger = logging.getLogger("audit")


class AuditService:
    def log_task(self, workspace_id: str, user_id: str, task_name: str) -> None:
        logger.info(
            "task_executed workspace_id=%s user_id=%s task_name=%s",
            workspace_id,
            user_id,
            task_name,
        )
