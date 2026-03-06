import importlib
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel


class _FakeRunner:
    def __init__(self, *args, **kwargs):
        _ = (args, kwargs)

    def chat(self, *, prompt: str, files: list[dict]):
        _ = (prompt, files)

        class _Result:
            text = "assistant reply"
            warnings = ["cleanup failed for file-1: boom"]

        return _Result()


def _load_main(tmp_path: Path):
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'http-tests.db'}"
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    SQLModel.metadata.clear()
    for module_name in ["app.main", "app.api.conversations", "app.api.files"]:
        sys.modules.pop(module_name, None)

    main = importlib.import_module("app.main")
    main.init_db()
    return main


def test_branching_consistency_and_selected_leaf_update(tmp_path: Path, monkeypatch) -> None:
    main = _load_main(tmp_path)
    monkeypatch.setattr("app.api.conversations.OpenAIRunner", _FakeRunner)

    with TestClient(main.app) as client:
        created = client.post("/api/conversations", json={"title": "branch flow"})
        assert created.status_code == 200
        conversation_id = created.json()["id"]

        first = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"text": "start"},
        )
        assert first.status_code == 200
        first_payload = first.json()
        user_message_id = first_payload["user_message_id"]

        branch = client.post(
            f"/api/messages/{user_message_id}/branch",
            json={"text": "branch"},
        )
        assert branch.status_code == 200
        branch_payload = branch.json()

        detail = client.get(f"/api/conversations/{conversation_id}")
        assert detail.status_code == 200
        detail_payload = detail.json()

        assert detail_payload["selected_leaf_message_id"] == branch_payload["assistant_message_id"]
        assert detail_payload["selected_path_messages"][-1]["id"] == branch_payload["assistant_message_id"]


def test_right_panel_exposes_warnings_and_run_fields(tmp_path: Path, monkeypatch) -> None:
    main = _load_main(tmp_path)
    monkeypatch.setattr("app.api.conversations.OpenAIRunner", _FakeRunner)

    with TestClient(main.app) as client:
        created = client.post("/api/conversations", json={"title": "warnings"})
        conversation_id = created.json()["id"]

        posted = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"text": "hello"},
        )
        assert posted.status_code == 200

        right_panel = client.get(f"/api/conversations/{conversation_id}/right-panel")
        assert right_panel.status_code == 200
        payload = right_panel.json()
        latest_run = payload["results"]["latest_runs"][0]
        assert latest_run["summary"] == "chat completed"
        assert latest_run["error_text"] is None
        assert latest_run["warnings"] == ["cleanup failed for file-1: boom"]
