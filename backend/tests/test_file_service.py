import importlib
import json
import os
import sys
from pathlib import Path

import pytest

from app.models import ConversationRun
from app.services.openai_runner import OpenAIResult
from fastapi import HTTPException
from sqlmodel import Session, SQLModel, select


def load_main(tmp_path: Path):
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'file_service.db'}"
    os.environ["STORAGE_LOCAL_ROOT"] = str(tmp_path / "storage")
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    SQLModel.metadata.clear()
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    main.init_db()
    return main


class FakeRunner:
    model_name = "test-model"

    def __init__(self):
        self.calls: list[dict] = []

    def chat(self, *, prompt: str, files: list[dict]) -> OpenAIResult:
        self.calls.append({"prompt": prompt, "files": files})
        return OpenAIResult(text="summary body", warnings=["cleanup failed for tmp: boom"])


def test_summarize_file_requires_included_binding(tmp_path: Path) -> None:
    main = load_main(tmp_path)

    with Session(main.engine) as session:
        conversation = main.create_conversation(main.ConversationCreate(title="files"), session)
        file_record = main.register_file(
            main.FileRegisterCreate(
                conversation_id=conversation.id,
                filename="spec.md",
                storage_backend="local",
                storage_key="conversations/spec.md",
            ),
            session,
        )

        with pytest.raises(HTTPException) as exc_info:
            main.summarize_file(conversation.id, file_record.id, session)

        assert exc_info.value.status_code == 400


def test_summarize_file_persists_runner_warnings(tmp_path: Path) -> None:
    main = load_main(tmp_path)
    from app.services.file_service import summarize_file

    runner = FakeRunner()

    with Session(main.engine) as session:
        conversation = main.create_conversation(main.ConversationCreate(title="files"), session)
        file_record = main.register_file(
            main.FileRegisterCreate(
                conversation_id=conversation.id,
                filename="spec.md",
                storage_backend="local",
                storage_key="conversations/spec.md",
                mime_type="text/markdown",
            ),
            session,
        )
        main.include_file(conversation.id, file_record.id, session)

        storage_file = Path(os.environ["STORAGE_LOCAL_ROOT"]) / "conversations/spec.md"
        storage_file.parent.mkdir(parents=True, exist_ok=True)
        storage_file.write_bytes(b"# spec")

        summary = summarize_file(session, conversation.id, file_record.id, runner)
        runs = session.exec(
            select(ConversationRun)
            .where(ConversationRun.conversation_id == conversation.id)
            .order_by(ConversationRun.created_at.desc())
        ).all()

        assert summary.content == "summary body"
        assert len(runner.calls) == 1
        assert runner.calls[0]["files"][0]["filename"] == "spec.md"
        assert json.loads(runs[0].warnings_json) == ["cleanup failed for tmp: boom"]
