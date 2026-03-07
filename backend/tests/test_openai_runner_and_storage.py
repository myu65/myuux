import importlib
import os
import sys
from pathlib import Path

from app.services.openai_runner import OpenAIRunner
from sqlmodel import Session, SQLModel


class FakeOpenAIClient:
    def __init__(self):
        self.created_payloads: list[dict] = []
        self.uploaded: list[str] = []
        self.deleted: list[str] = []

    def create_response(self, payload: dict) -> dict:
        self.created_payloads.append(payload)
        return {"output_text": "ok"}

    def upload_file(self, *, filename: str, content: bytes, content_type: str | None) -> str:
        _ = (content, content_type)
        file_id = f"temp-{filename}"
        self.uploaded.append(file_id)
        return file_id

    def delete_file(self, file_id: str) -> None:
        self.deleted.append(file_id)
        if file_id.endswith("image.png"):
            raise RuntimeError("delete failed")


class _RunnerResult:
    text = "summary"
    warnings: list[str] = []


class _NoopRunner:
    model_name = "test-model"

    def chat(self, *, prompt: str, files: list[dict]):
        _ = (prompt, files)
        return _RunnerResult()


def _load_main(tmp_path: Path):
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'storage-tests.db'}"
    os.environ["STORAGE_LOCAL_ROOT"] = str(tmp_path / "storage")
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    SQLModel.metadata.clear()
    for module_name in ["app.main", "app.services.conversation_service", "app.services.file_service"]:
        sys.modules.pop(module_name, None)

    main = importlib.import_module("app.main")
    main.init_db()
    return main


def test_openai_runner_temp_file_cleanup_lifecycle() -> None:
    client = FakeOpenAIClient()
    runner = OpenAIRunner(client=client, model_name="test-model")

    result = runner.chat(
        prompt="hello",
        files=[
            {"filename": "notes.md", "content": b"small text", "content_type": "text/markdown"},
            {"filename": "image.png", "content": b"\x89PNG\r\n\x1a\n", "content_type": "image/png"},
        ],
    )

    assert result.text == "ok"
    assert client.uploaded == ["temp-image.png"]
    assert client.deleted == ["temp-image.png"]
    assert result.warnings and "cleanup failed for temp-image.png" in result.warnings[0]

    payload = client.created_payloads[0]
    assert payload["store"] is False


def test_list_included_files_reads_real_storage_bytes(tmp_path: Path) -> None:
    main = _load_main(tmp_path)
    from app.services.conversation_service import list_included_files

    storage_file = Path(os.environ["STORAGE_LOCAL_ROOT"]) / "conversations/spec.md"
    storage_file.parent.mkdir(parents=True, exist_ok=True)
    storage_file.write_bytes(b"# Real Content\n")

    with Session(main.engine) as session:
        conversation = main.create_conversation(main.ConversationCreate(title="files"), session)
        file_record = main.register_file(
            main.FileRegisterCreate(
                conversation_id=conversation.id,
                filename="spec.md",
                storage_backend="local",
                storage_key="conversations/spec.md",
                mime_type="text/markdown",
                size_bytes=15,
            ),
            session,
        )
        main.include_file(conversation.id, file_record.id, session)

        included = list_included_files(session, conversation.id)

    assert len(included) == 1
    assert included[0]["content"] == b"# Real Content\n"


def test_summarize_file_passes_real_file_content(tmp_path: Path) -> None:
    main = _load_main(tmp_path)
    from app.services.file_service import summarize_file

    storage_file = Path(os.environ["STORAGE_LOCAL_ROOT"]) / "conversations/report.txt"
    storage_file.parent.mkdir(parents=True, exist_ok=True)
    storage_file.write_bytes(b"hello storage")


    with Session(main.engine) as session:
        conversation = main.create_conversation(main.ConversationCreate(title="files"), session)
        file_record = main.register_file(
            main.FileRegisterCreate(
                conversation_id=conversation.id,
                filename="report.txt",
                storage_backend="local",
                storage_key="conversations/report.txt",
                mime_type="text/plain",
                size_bytes=13,
            ),
            session,
        )
        main.include_file(conversation.id, file_record.id, session)

        captured: dict = {}

        class _CaptureRunner(_NoopRunner):
            def chat(self, *, prompt: str, files: list[dict]):
                captured["prompt"] = prompt
                captured["files"] = files
                return _RunnerResult()

        summarize_file(session, conversation.id, file_record.id, _CaptureRunner())

    assert captured["files"][0]["content"] == b"hello storage"
