from app.db import get_session
from app.models import ConversationArtifact, ConversationRun
from fastapi import Depends
from sqlmodel import Session, select


def list_conversation_runs(conversation_id: str, session: Session = Depends(get_session)) -> list[ConversationRun]:
    return session.exec(select(ConversationRun).where(ConversationRun.conversation_id == conversation_id)).all()


def list_conversation_artifacts(
    conversation_id: str, session: Session = Depends(get_session)
) -> list[ConversationArtifact]:
    return session.exec(
        select(ConversationArtifact).where(ConversationArtifact.conversation_id == conversation_id)
    ).all()


def register_routes(app):
    app.get("/api/conversations/{conversation_id}/runs", response_model=list[ConversationRun])(list_conversation_runs)
    app.get("/api/conversations/{conversation_id}/artifacts", response_model=list[ConversationArtifact])(
        list_conversation_artifacts
    )
