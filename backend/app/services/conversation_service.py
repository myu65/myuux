import json
import os
from datetime import datetime

from app.models import Conversation, ConversationMessage, ConversationRun, FileBinding, FileRecord
from app.schemas import MessageCreateResult, MessagePathView
from app.services.content_service import message_text, serialize_message_text
from app.services.openai_runner import OpenAIRunner
from app.services.storage import StorageManager
from fastapi import HTTPException
from sqlmodel import Session, select

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5.4")


def build_message_path(messages_by_id: dict[str, ConversationMessage], leaf_id: str) -> list[ConversationMessage]:
    path: list[ConversationMessage] = []
    current_id = leaf_id
    while current_id:
        current = messages_by_id.get(current_id)
        if not current:
            break
        path.append(current)
        current_id = current.parent_message_id or ""
    path.reverse()
    return path


def to_path_view(message: ConversationMessage) -> MessagePathView:
    return MessagePathView(
        id=message.id,
        parent_message_id=message.parent_message_id,
        role=message.role,
        text=message_text(message.content_json),
    )


def list_included_files(session: Session, conversation_id: str) -> list[dict]:
    bindings = session.exec(
        select(FileBinding).where(
            FileBinding.conversation_id == conversation_id,
            FileBinding.included_in_context == True,  # noqa: E712
        )
    ).all()
    files: list[dict] = []
    storage = StorageManager()
    for binding in bindings:
        file_record = session.get(FileRecord, binding.file_id)
        if file_record and file_record.conversation_id == conversation_id:
            content = storage.read_bytes(backend_name=file_record.storage_backend, key=file_record.storage_key)
            files.append(
                {
                    "filename": file_record.filename,
                    "content": content,
                    "content_type": file_record.mime_type,
                }
            )
    return files


def _mark_run_failed(session: Session, run: ConversationRun, exc: Exception, warnings: list[str] | None = None) -> None:
    run.status = "failed"
    run.error_text = str(exc)
    run.finished_at = datetime.utcnow()
    run.warnings_json = json.dumps(warnings or [])
    run.updated_at = datetime.utcnow()
    session.add(run)
    session.commit()


def create_message_with_assistant(
    session: Session, *, conversation_id: str, text: str, parent_message_id: str | None, runner: OpenAIRunner
) -> MessageCreateResult:
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="conversation not found")
    user_parent_id = parent_message_id or conversation.selected_leaf_message_id
    user_message = ConversationMessage(
        conversation_id=conversation_id,
        parent_message_id=user_parent_id,
        role="user",
        content_json=serialize_message_text(text),
    )
    session.add(user_message)
    session.commit()
    session.refresh(user_message)

    run = ConversationRun(
        conversation_id=conversation_id,
        message_id=user_message.id,
        branch_leaf_message_id=user_message.id,
        run_type="chat",
        status="running",
        model_name=MODEL_NAME,
        started_at=datetime.utcnow(),
    )
    session.add(run)
    session.commit()

    try:
        result = runner.chat(prompt=text, files=list_included_files(session, conversation_id))
    except Exception as exc:  # noqa: BLE001
        _mark_run_failed(session, run, exc)
        raise HTTPException(status_code=502, detail="model run failed") from exc

    try:
        assistant_message = ConversationMessage(
            conversation_id=conversation_id,
            parent_message_id=user_message.id,
            role="assistant",
            content_json=serialize_message_text(result.text),
        )
        session.add(assistant_message)
        session.commit()
        session.refresh(assistant_message)
    except Exception as exc:  # noqa: BLE001
        _mark_run_failed(session, run, exc, result.warnings)
        raise

    run.status = "completed"
    run.finished_at = datetime.utcnow()
    run.summary = "chat completed"
    run.branch_leaf_message_id = assistant_message.id
    run.warnings_json = json.dumps(result.warnings)
    run.updated_at = datetime.utcnow()
    conversation.selected_leaf_message_id = assistant_message.id
    conversation.updated_at = datetime.utcnow()
    session.add(run)
    session.add(conversation)
    session.commit()
    session.refresh(run)
    return MessageCreateResult(
        user_message_id=user_message.id, assistant_message_id=assistant_message.id, run_id=run.id
    )


def regenerate_message(session: Session, message_id: str, runner: OpenAIRunner) -> ConversationMessage:
    target_message = session.get(ConversationMessage, message_id)
    if not target_message:
        raise HTTPException(status_code=404, detail="message not found")
    if target_message.role != "user":
        raise HTTPException(status_code=400, detail="regenerate target must be a user message")

    result = runner.chat(
        prompt=message_text(target_message.content_json),
        files=list_included_files(session, target_message.conversation_id),
    )
    assistant = ConversationMessage(
        conversation_id=target_message.conversation_id,
        parent_message_id=target_message.id,
        role="assistant",
        content_json=serialize_message_text(result.text),
    )
    session.add(assistant)
    session.commit()
    session.refresh(assistant)

    run = ConversationRun(
        conversation_id=target_message.conversation_id,
        message_id=assistant.id,
        branch_leaf_message_id=assistant.id,
        run_type="chat",
        status="completed",
        model_name=MODEL_NAME,
        summary="regenerate completed",
        warnings_json=json.dumps(result.warnings),
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
    )
    session.add(run)

    conversation = session.get(Conversation, target_message.conversation_id)
    if conversation:
        conversation.selected_leaf_message_id = assistant.id
        conversation.updated_at = datetime.utcnow()
        session.add(conversation)

    session.commit()
    return assistant
