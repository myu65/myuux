import json

from app.services.content_service import message_text, serialize_message_text
from app.services.conversation_service import build_message_path
from app.services.openai_runner import OpenAIRunner


class DummyMessage:
    def __init__(self, id: str, parent_message_id: str | None):
        self.id = id
        self.parent_message_id = parent_message_id


class FakeClient:
    def __init__(self):
        self.deleted: list[str] = []

    def create_response(self, payload: dict) -> dict:
        assert payload["store"] is False
        return {"output_text": "ok"}

    def upload_file(self, *, filename: str, content: bytes, content_type: str | None) -> str:
        return f"file-{filename}"

    def delete_file(self, file_id: str) -> None:
        self.deleted.append(file_id)
        if "fail" in file_id:
            raise RuntimeError("cannot delete")


def test_message_path_reconstruction() -> None:
    a = DummyMessage("a", None)
    b = DummyMessage("b", "a")
    c = DummyMessage("c", "b")
    path = build_message_path({"a": a, "b": b, "c": c}, "c")
    assert [node.id for node in path] == ["a", "b", "c"]


def test_content_json_serialization_is_safe() -> None:
    raw = 'quote " and newline\n and {json}'
    payload = serialize_message_text(raw)
    parsed = json.loads(payload)
    assert parsed["parts"][0]["text"] == raw
    assert message_text(payload) == raw


def test_openai_runner_cleanup_warning_lifecycle() -> None:
    client = FakeClient()
    runner = OpenAIRunner(client=client, model_name="test-model")
    result = runner.chat(
        prompt="hello",
        files=[
            {"filename": "ok.png", "content": b"ok", "content_type": "image/png"},
            {"filename": "fail.png", "content": b"bad", "content_type": "image/png"},
        ],
    )
    assert result.text == "ok"
    assert any("cleanup failed" in warning for warning in result.warnings)
    assert client.deleted == ["file-ok.png", "file-fail.png"]
