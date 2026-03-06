from datetime import datetime
from uuid import uuid4

from app.db import get_session
from app.models import Conversation, ConversationRun, FileRecord, FileSummary
from app.schemas import FileRegisterCreate, FileView, RightPanelResponse, UploadUrlCreate
from app.services.file_service import get_or_create_binding
from app.services.file_service import summarize_file as summarize_file_service
from app.services.openai_runner import OpenAIRunner
from fastapi import Depends, HTTPException
from sqlmodel import Session, select


def create_upload_url(payload: UploadUrlCreate):
    key = f"conversations/{uuid4()}-{payload.filename}"
    return {"storage_backend": "local", "storage_key": key, "upload_method": "direct_register"}


def register_file(payload: FileRegisterCreate, session: Session = Depends(get_session)) -> FileRecord:
    conversation = session.get(Conversation, payload.conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="conversation not found")
    file_record = FileRecord(
        conversation_id=payload.conversation_id,
        filename=payload.filename,
        storage_backend=payload.storage_backend,
        storage_key=payload.storage_key,
        mime_type=payload.mime_type,
        size_bytes=payload.size_bytes,
    )
    session.add(file_record)
    session.commit()
    session.refresh(file_record)
    get_or_create_binding(session, payload.conversation_id, file_record.id)
    return file_record


def list_conversation_files(conversation_id: str, session: Session = Depends(get_session)) -> list[FileView]:
    files = session.exec(select(FileRecord).where(FileRecord.conversation_id == conversation_id)).all()
    views: list[FileView] = []
    for file_record in files:
        binding = get_or_create_binding(session, conversation_id, file_record.id)
        views.append(
            FileView(
                id=file_record.id,
                conversation_id=file_record.conversation_id,
                filename=file_record.filename,
                storage_backend=file_record.storage_backend,
                storage_key=file_record.storage_key,
                mime_type=file_record.mime_type,
                size_bytes=file_record.size_bytes,
                included_in_context=binding.included_in_context,
            )
        )
    return views


def include_file(conversation_id: str, file_id: str, session: Session = Depends(get_session)):
    binding = get_or_create_binding(session, conversation_id, file_id)
    binding.included_in_context = True
    binding.updated_at = datetime.utcnow()
    session.add(binding)
    session.commit()
    session.refresh(binding)
    return binding


def exclude_file(conversation_id: str, file_id: str, session: Session = Depends(get_session)):
    binding = get_or_create_binding(session, conversation_id, file_id)
    binding.included_in_context = False
    binding.updated_at = datetime.utcnow()
    session.add(binding)
    session.commit()
    session.refresh(binding)
    return binding


def summarize_file(conversation_id: str, file_id: str, session: Session = Depends(get_session)) -> FileSummary:
    return summarize_file_service(session, conversation_id, file_id, OpenAIRunner())


def get_conversation_right_panel(conversation_id: str, session: Session = Depends(get_session)) -> RightPanelResponse:
    runs = session.exec(
        select(ConversationRun)
        .where(ConversationRun.conversation_id == conversation_id)
        .order_by(ConversationRun.created_at.desc())
    ).all()
    files = list_conversation_files(conversation_id, session)
    latest_file_summary = session.exec(
        select(FileSummary)
        .where(FileSummary.conversation_id == conversation_id)
        .order_by(FileSummary.created_at.desc())
    ).first()
    return RightPanelResponse(
        results={
            "latest_runs": [
                {
                    "id": run.id,
                    "run_type": run.run_type,
                    "status": run.status,
                    "summary": run.summary,
                    "error_text": run.error_text,
                }
                for run in runs[:10]
            ],
            "latest_artifacts": [],
        },
        files=files,
        summaries={
            "conversation_summary": None,
            "branch_summary": None,
            "latest_file_summary": latest_file_summary.content if latest_file_summary else None,
        },
        agent={"model": OpenAIRunner().model_name, "store": False},
    )


def register_routes(app):
    app.post("/api/files/upload-url")(create_upload_url)
    app.post("/api/files/register", response_model=FileRecord)(register_file)
    app.get("/api/conversations/{conversation_id}/files", response_model=list[FileView])(list_conversation_files)
    app.post("/api/conversations/{conversation_id}/files/{file_id}/include")(include_file)
    app.post("/api/conversations/{conversation_id}/files/{file_id}/exclude")(exclude_file)
    app.post("/api/conversations/{conversation_id}/files/{file_id}/summarize", response_model=FileSummary)(
        summarize_file
    )
    app.get("/api/conversations/{conversation_id}/right-panel", response_model=RightPanelResponse)(
        get_conversation_right_panel
    )
