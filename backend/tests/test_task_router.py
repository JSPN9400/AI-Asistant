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
    assert result["result"]["assistant_reply"]


def test_browser_navigation_route() -> None:
    router = TaskRouter()
    result = router.handle(
        "open youtube",
        {
            "workspace_id": "demo-workspace",
            "user_id": "user-1",
            "attachments": [],
            "context": {},
        },
    )
    assert result["task"] == "browser_navigator"
    assert result["result"]["status"] == "success"
    assert result["result"]["action"] == "open_url"
    assert result["result"]["assistant_reply"]


def test_desktop_control_route() -> None:
    router = TaskRouter()
    result = router.handle(
        "open chrome",
        {
            "workspace_id": "demo-workspace",
            "user_id": "user-1",
            "attachments": [],
            "context": {},
        },
    )
    assert result["task"] == "desktop_control"
    assert "cannot open apps on your computer" in result["result"]["message"]
    assert result["result"]["assistant_reply"]


def test_general_question_route() -> None:
    router = TaskRouter()
    result = router.handle(
        "Who is the prime minister of India?",
        {
            "workspace_id": "demo-workspace",
            "user_id": "user-1",
            "attachments": [],
            "context": {},
        },
    )
    assert result["task"] == "general_assistant"
    assert result["result"]["assistant_reply"]
