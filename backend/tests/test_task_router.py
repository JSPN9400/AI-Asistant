from app.services.task_router import TaskRouter


def test_sales_report_route() -> None:
    router = TaskRouter()
    result = router.handle(
        "Create a weekly sales report from this file.",
        {
            "workspace_id": "demo-workspace",
            "user_id": "user-1",
            "attachments": ["file-1"],
            "context": {},
        },
    )
    assert result["task"] == "sales_report_generator"
    assert result["result"]["status"] == "success"
