from pathlib import Path

from app.db.models import UploadedFile
from app.db.repositories.files import UploadedFileRepository
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


def test_floor_wise_report_generation(tmp_path: Path) -> None:
    router = TaskRouter()
    csv_path = tmp_path / "floor-metrics.csv"
    csv_path.write_text(
        "Floor,Area,Cost,Units\n"
        "Ground,1200,10000,12\n"
        "Ground,800,5000,8\n"
        "First,1000,9000,10\n",
        encoding="utf-8",
    )
    file_id = "test-floor-report"
    UploadedFileRepository().create(
        UploadedFile(
            id=file_id,
            workspace_id="demo-workspace",
            uploaded_by="user-1",
            filename="floor-metrics.csv",
            storage_path=str(csv_path),
            content_type="text/csv",
        )
    )

    result = router.handle(
        "Calculate for every floor and make a good PDF report.",
        {
            "workspace_id": "demo-workspace",
            "user_id": "user-1",
            "attachments": [file_id],
            "context": {},
        },
    )

    assert result["task"] == "sales_report_generator"
    assert result["result"]["status"] == "success"
    assert result["result"]["group_by"] == "Floor"
    assert result["result"]["totals"]["Area"] == 3000.0
    assert len(result["result"]["floor_breakdown"]) == 2
    assert "html" in result["result"]["report_files"]
    assert "json" in result["result"]["report_files"]
    assert "text" in result["result"]["report_files"]
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
