from datetime import datetime

from app.models import Conversation, ConversationRun, FileBinding, FileRecord, FileSummary
from app.services.openai_runner import OpenAIRunner
from fastapi import HTTPException
from sqlmodel import Session, select


def get_or_create_binding(session: Session, conversation_id: str, file_id: str) -> FileBinding:
    statement = select(FileBinding).where(
        FileBinding.conversation_id == conversation_id,
        FileBinding.file_id == file_id,
    )
    binding = session.exec(statement).first()
    if binding:
        return binding
    binding = FileBinding(conversation_id=conversation_id, file_id=file_id)
    session.add(binding)
    session.commit()
    session.refresh(binding)
    return binding


def summarize_file(session: Session, conversation_id: str, file_id: str, runner: OpenAIRunner) -> FileSummary:
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="conversation not found")

    file_record = session.get(FileRecord, file_id)
    if not file_record or file_record.conversation_id != conversation_id:
        raise HTTPException(status_code=404, detail="file not found")

    binding = get_or_create_binding(session, conversation_id, file_id)
    if not binding.included_in_context:
        raise HTTPException(status_code=400, detail="file must be included before summarize")

    result = runner.chat(prompt=f"Summarize file: {file_record.filename}", files=[])
    run = ConversationRun(
        conversation_id=conversation_id,
        message_id=None,
        branch_leaf_message_id=None,
        run_type="summarize_file",
        status="completed",
        model_name=runner.model_name,
        summary=f"summary generated for {file_record.filename}",
        warnings_json="[]",
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
    )
    session.add(run)

    summary = FileSummary(
        file_id=file_id,
        conversation_id=conversation_id,
        summary_type="short",
        content=result.text,
    )
    session.add(summary)
    session.commit()
    session.refresh(summary)
    return summary
