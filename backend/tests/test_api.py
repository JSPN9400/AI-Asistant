from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
HEADERS = {
    "x-api-key": "replace-in-prod",
    "x-user-id": "test-user",
    "x-workspace-id": "demo-workspace",
}


def test_healthcheck() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_system_status() -> None:
    response = client.get("/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "llm" in data
    assert "provider" in data["llm"]
    assert "state" in data["llm"]


def test_system_llm_configuration_roundtrip() -> None:
    current = client.get("/system/llm", headers=HEADERS)
    assert current.status_code == 200
    payload = current.json()
    assert payload["provider"]
    assert payload["model"]

    update_response = client.post(
        "/system/llm",
        headers=HEADERS,
        json={
            "provider": "ollama",
            "model": payload["model"],
            "enable_cloud_reasoner": True,
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["provider"] == "ollama"
    assert updated["model"] == payload["model"]
    assert "state" in updated["status"]


def test_login_and_bearer_access() -> None:
    login_response = client.post(
        "/auth/login",
        json={
            "email": "demo@company.com",
            "password": "demo-pass",
            "workspace_id": "demo-workspace",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.get(
        "/plugins/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()


def test_task_and_history_flow() -> None:
    run_response = client.post(
        "/tasks/",
        headers=HEADERS,
        json={
            "user_input": "Create a weekly sales report from this data.",
            "workspace_id": "demo-workspace",
            "attachments": [],
            "context": {},
        },
    )
    assert run_response.status_code == 200
    run_data = run_response.json()
    assert run_data["task"] == "sales_report_generator"
    assert run_data["task_id"]

    history_response = client.get(
        "/tasks/history",
        headers=HEADERS,
        params={"workspace_id": "demo-workspace", "limit": 5},
    )
    assert history_response.status_code == 200
    history = history_response.json()
    assert history
    assert history[0]["task"] == "sales_report_generator"
