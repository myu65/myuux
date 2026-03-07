import importlib
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel


class _SuccessRunner:
    def __init__(self, *args, **kwargs):
        _ = (args, kwargs)

    def chat(self, *, prompt: str, files: list[dict]):
        _ = (prompt, files)

        class _Result:
            text = "assistant reply"
            warnings = ["cleanup failed for file-1: boom"]

        return _Result()


class _FailRunner:
    def __init__(self, *args, **kwargs):
        _ = (args, kwargs)

    def chat(self, *, prompt: str, files: list[dict]):
        _ = (prompt, files)
        raise RuntimeError("openai unavailable")


class _CleanupWarningRunner:
    model_name = "test-model"

    def __init__(self, *args, **kwargs):
        _ = (args, kwargs)

    def chat(self, *, prompt: str, files: list[dict]):
        _ = prompt
        assert len(files) == 1
        assert files[0]["content"] == b"# spec"

        class _Result:
            text = "assistant with include"
            warnings = ["cleanup failed for temp-file-1: cannot delete"]

        return _Result()


def _load_main(tmp_path: Path):
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'http-tests.db'}"
    os.environ["STORAGE_LOCAL_ROOT"] = str(tmp_path / "storage")
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    SQLModel.metadata.clear()
    for module_name in ["app.main", "app.api.conversations", "app.api.files"]:
        sys.modules.pop(module_name, None)

    main = importlib.import_module("app.main")
    main.init_db()
    return main


def test_http_chat_run_success_records_completed_run(tmp_path: Path, monkeypatch) -> None:
    main = _load_main(tmp_path)
    monkeypatch.setattr("app.api.conversations.OpenAIRunner", _SuccessRunner)

    with TestClient(main.app) as client:
        created = client.post("/api/conversations", json={"title": "chat success"})
        conversation_id = created.json()["id"]

        posted = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"text": "hello"},
        )
        assert posted.status_code == 200

        runs = client.get(f"/api/conversations/{conversation_id}/runs")
        assert runs.status_code == 200
        run = runs.json()[0]
        assert run["status"] == "completed"
        assert run["error_text"] is None


def test_http_chat_run_failure_marks_run_failed(tmp_path: Path, monkeypatch) -> None:
    main = _load_main(tmp_path)
    monkeypatch.setattr("app.api.conversations.OpenAIRunner", _FailRunner)

    with TestClient(main.app) as client:
        created = client.post("/api/conversations", json={"title": "chat fail"})
        conversation_id = created.json()["id"]

        posted = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"text": "hello"},
        )
        assert posted.status_code == 502

        runs = client.get(f"/api/conversations/{conversation_id}/runs")
        assert runs.status_code == 200
        run = runs.json()[0]
        assert run["status"] == "failed"
        assert "openai unavailable" in (run["error_text"] or "")
        assert run["warnings"] == []


def test_regenerate_keeps_consistent_included_context_policy(tmp_path: Path, monkeypatch) -> None:
    main = _load_main(tmp_path)
    monkeypatch.setattr("app.api.conversations.OpenAIRunner", _SuccessRunner)

    with TestClient(main.app) as client:
        created = client.post("/api/conversations", json={"title": "regenerate"})
        conversation_id = created.json()["id"]

        first = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"text": "seed"},
        )
        assert first.status_code == 200
        user_message_id = first.json()["user_message_id"]

        regenerated = client.post(f"/api/messages/{user_message_id}/regenerate")
        assert regenerated.status_code == 200
        assert regenerated.json()["parent_message_id"] == user_message_id

        detail = client.get(f"/api/conversations/{conversation_id}")
        path = detail.json()["selected_path_messages"]
        assert path[-1]["id"] == regenerated.json()["id"]


def test_http_cleanup_warning_lifecycle_exposed_in_right_panel(tmp_path: Path, monkeypatch) -> None:
    main = _load_main(tmp_path)
    monkeypatch.setattr("app.api.conversations.OpenAIRunner", _CleanupWarningRunner)

    with TestClient(main.app) as client:
        created = client.post("/api/conversations", json={"title": "cleanup"})
        conversation_id = created.json()["id"]

        register = client.post(
            "/api/files/register",
            json={
                "conversation_id": conversation_id,
                "filename": "spec.md",
                "storage_backend": "local",
                "storage_key": "conversations/spec.md",
                "mime_type": "text/markdown",
                "size_bytes": 6,
            },
        )
        assert register.status_code == 200
        file_id = register.json()["id"]

        storage_file = Path(os.environ["STORAGE_LOCAL_ROOT"]) / "conversations/spec.md"
        storage_file.parent.mkdir(parents=True, exist_ok=True)
        storage_file.write_bytes(b"# spec")

        include = client.post(f"/api/conversations/{conversation_id}/files/{file_id}/include")
        assert include.status_code == 200

        posted = client.post(f"/api/conversations/{conversation_id}/messages", json={"text": "use file"})
        assert posted.status_code == 200

        right_panel = client.get(f"/api/conversations/{conversation_id}/right-panel")
        assert right_panel.status_code == 200
        latest_run = right_panel.json()["results"]["latest_runs"][0]
        assert latest_run["warnings"] == ["cleanup failed for temp-file-1: cannot delete"]


def test_branching_consistency_and_selected_leaf_update(tmp_path: Path, monkeypatch) -> None:
    main = _load_main(tmp_path)
    monkeypatch.setattr("app.api.conversations.OpenAIRunner", _SuccessRunner)

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
    monkeypatch.setattr("app.api.conversations.OpenAIRunner", _SuccessRunner)

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
