import importlib
import os
from pathlib import Path

from fastapi.testclient import TestClient


def build_client(tmp_path: Path) -> TestClient:
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'test.db'}"
    import app.main as main

    main = importlib.reload(main)
    main.init_db()
    return TestClient(main.app)


def test_create_and_list_workspaces(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    create_res = client.post("/api/workspaces", json={"name": "demo"})
    assert create_res.status_code == 200
    assert create_res.json()["name"] == "demo"

    list_res = client.get("/api/workspaces")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1


def test_chat_creates_run(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    workspace_id = client.post("/api/workspaces", json={"name": "demo"}).json()["id"]

    chat_res = client.post(
        f"/api/workspaces/{workspace_id}/chat",
        json={"prompt": "revise this", "skill": "ppt_revise"},
    )
    assert chat_res.status_code == 200

    body = chat_res.json()
    assert "message_id" in body
    assert "run_id" in body
