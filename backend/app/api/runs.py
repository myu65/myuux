import json

from app.db import get_session
from app.models import ConversationArtifact, ConversationRun
from app.schemas import ArtifactResultView, RunResultView
from fastapi import Depends
from sqlmodel import Session, select


def _parse_warnings(warnings_json: str) -> list[str]:
    try:
        data = json.loads(warnings_json)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def list_conversation_runs(conversation_id: str, session: Session = Depends(get_session)) -> list[RunResultView]:
    runs = session.exec(select(ConversationRun).where(ConversationRun.conversation_id == conversation_id)).all()
    return [
        RunResultView(
            id=run.id,
            run_type=run.run_type,
            status=run.status,
            summary=run.summary,
            error_text=run.error_text,
            warnings=_parse_warnings(run.warnings_json),
        )
        for run in runs
    ]


def list_conversation_artifacts(
    conversation_id: str, session: Session = Depends(get_session)
) -> list[ArtifactResultView]:
    artifacts = session.exec(
        select(ConversationArtifact).where(ConversationArtifact.conversation_id == conversation_id)
    ).all()
    views: list[ArtifactResultView] = []
    for artifact in artifacts:
        try:
            metadata = json.loads(artifact.metadata_json)
        except json.JSONDecodeError:
            metadata = {}
        views.append(
            ArtifactResultView(
                id=artifact.id,
                title=artifact.title,
                artifact_type=artifact.artifact_type,
                storage_key=artifact.storage_key,
                storage_backend=artifact.storage_backend,
                metadata=metadata if isinstance(metadata, dict) else {},
            )
        )
    return views


def register_routes(app):
    app.get("/api/conversations/{conversation_id}/runs", response_model=list[RunResultView])(list_conversation_runs)
    app.get("/api/conversations/{conversation_id}/artifacts", response_model=list[ArtifactResultView])(
        list_conversation_artifacts
    )
