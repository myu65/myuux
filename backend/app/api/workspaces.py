import json
from datetime import datetime
from typing import Generator

from app.db import get_session
from app.models import Artifact, Message, Run, Workspace
from app.schemas import (
    ArtifactVersionChain,
    ChatCreate,
    FeatureCatalog,
    RunComplete,
    RunCompleteResponse,
    RunCreate,
    WorkspaceCreate,
)
from fastapi import Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select


def create_workspace(payload: WorkspaceCreate, session: Session = Depends(get_session)) -> Workspace:
    workspace = Workspace(name=payload.name)
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace


def list_workspaces(session: Session = Depends(get_session)) -> list[Workspace]:
    return session.exec(select(Workspace).order_by(Workspace.created_at.desc())).all()


def get_workspace(workspace_id: int, session: Session = Depends(get_session)) -> Workspace:
    workspace = session.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="workspace not found")
    return workspace


def upload_file(workspace_id: int, file: UploadFile = File(...), session: Session = Depends(get_session)) -> Artifact:
    workspace = session.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="workspace not found")
    artifact = Artifact(
        workspace_id=workspace_id,
        path=f"raw/{file.filename}",
        type=file.filename.split(".")[-1],
        version_group=file.filename,
        version_no=1,
    )
    session.add(artifact)
    session.commit()
    session.refresh(artifact)
    return artifact


def list_artifacts(workspace_id: int, session: Session = Depends(get_session)) -> list[Artifact]:
    return session.exec(select(Artifact).where(Artifact.workspace_id == workspace_id)).all()


def create_run(workspace_id: int, payload: RunCreate, session: Session = Depends(get_session)) -> Run:
    run = Run(
        workspace_id=workspace_id,
        skill_name=payload.skill,
        prompt=payload.prompt,
        input_artifact_ids=json.dumps(payload.input_artifact_ids),
        params_json=json.dumps(payload.params),
        status="running",
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def complete_run(run_id: int, payload: RunComplete, session: Session = Depends(get_session)) -> RunCompleteResponse:
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    latest_in_group = session.exec(
        select(Artifact)
        .where(Artifact.workspace_id == run.workspace_id, Artifact.version_group == payload.output_filename)
        .order_by(Artifact.version_no.desc())
    ).first()
    next_version = 1 if latest_in_group is None else latest_in_group.version_no + 1
    artifact = Artifact(
        workspace_id=run.workspace_id,
        path=f"out/{payload.output_filename}",
        type=payload.artifact_type,
        version_group=payload.output_filename,
        version_no=next_version,
        source_run_id=run.id,
    )
    session.add(artifact)
    session.commit()
    session.refresh(artifact)
    run.status = "success"
    run.finished_at = datetime.utcnow()
    run.output_artifact_ids = json.dumps([artifact.id])
    session.add(run)
    session.commit()
    return RunCompleteResponse(run_id=run.id, status=run.status, output_artifact=artifact)


def publish_artifact(artifact_id: int, session: Session = Depends(get_session)) -> Artifact:
    artifact = session.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="artifact not found")
    artifact.published_at = datetime.utcnow()
    session.add(artifact)
    session.commit()
    session.refresh(artifact)
    return artifact


def get_artifact_version_chain(artifact_id: int, session: Session = Depends(get_session)) -> ArtifactVersionChain:
    artifact = session.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="artifact not found")
    previous_artifact = session.exec(
        select(Artifact)
        .where(
            Artifact.workspace_id == artifact.workspace_id,
            Artifact.version_group == artifact.version_group,
            Artifact.version_no < artifact.version_no,
        )
        .order_by(Artifact.version_no.desc())
    ).first()
    next_artifact = session.exec(
        select(Artifact)
        .where(
            Artifact.workspace_id == artifact.workspace_id,
            Artifact.version_group == artifact.version_group,
            Artifact.version_no > artifact.version_no,
        )
        .order_by(Artifact.version_no.asc())
    ).first()
    return ArtifactVersionChain(artifact=artifact, previous_artifact=previous_artifact, next_artifact=next_artifact)


def list_runs(workspace_id: int, session: Session = Depends(get_session)) -> list[Run]:
    statement = select(Run).where(Run.workspace_id == workspace_id).order_by(Run.created_at.desc())
    return session.exec(statement).all()


def get_run(run_id: int, session: Session = Depends(get_session)) -> Run:
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return run


def chat_trigger(workspace_id: int, payload: ChatCreate, session: Session = Depends(get_session)):
    message = Message(workspace_id=workspace_id, role="user", content=payload.prompt)
    session.add(message)
    session.commit()
    run = create_run(
        workspace_id, RunCreate(skill=payload.skill, prompt=payload.prompt, input_artifact_ids=[], params={}), session
    )
    return {"message_id": message.id, "run_id": run.id}


def run_events(run_id: int):
    def event_stream() -> Generator[str, None, None]:
        steps = [
            "validate inputs",
            "load template",
            "generate slide outline",
            "render chart",
            "write out/proposal_v3.pptx",
        ]
        for idx, step in enumerate(steps, start=1):
            yield f'event: log\\ndata: {{"run_id": {run_id}, "step": {idx}, "message": "{step}"}}\\n\\n'
        yield 'event: done\\ndata: {"status": "success"}\\n\\n'

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def get_feature_catalog() -> FeatureCatalog:
    return FeatureCatalog(
        version="1.1",
        extension_points=[
            "workspace_lifecycle",
            "artifact_upload",
            "run_creation",
            "run_completion",
            "artifact_publish",
            "run_events_stream",
            "chat_trigger",
        ],
        notes=[
            "Use /api/workspaces/{id}/runs for reproducible execution records.",
            "Use /api/runs/{run_id}/events for live log streaming.",
            "Store generated files under out/ and keep raw uploads immutable.",
            "Use /api/runs/{run_id}/complete to register generated artifacts.",
            "Use /api/artifacts/{artifact_id}/publish for explicit publication.",
        ],
    )


def register_routes(app):
    app.post("/api/workspaces", response_model=Workspace)(create_workspace)
    app.get("/api/workspaces", response_model=list[Workspace])(list_workspaces)
    app.get("/api/workspaces/{workspace_id}", response_model=Workspace)(get_workspace)
    app.post("/api/workspaces/{workspace_id}/upload", response_model=Artifact)(upload_file)
    app.get("/api/workspaces/{workspace_id}/artifacts", response_model=list[Artifact])(list_artifacts)
    app.post("/api/workspaces/{workspace_id}/runs", response_model=Run)(create_run)
    app.post("/api/runs/{run_id}/complete", response_model=RunCompleteResponse)(complete_run)
    app.post("/api/artifacts/{artifact_id}/publish", response_model=Artifact)(publish_artifact)
    app.get("/api/artifacts/{artifact_id}/chain", response_model=ArtifactVersionChain)(get_artifact_version_chain)
    app.get("/api/workspaces/{workspace_id}/runs", response_model=list[Run])(list_runs)
    app.get("/api/runs/{run_id}", response_model=Run)(get_run)
    app.post("/api/workspaces/{workspace_id}/chat")(chat_trigger)
    app.get("/api/runs/{run_id}/events")(run_events)
    app.get("/api/features", response_model=FeatureCatalog)(get_feature_catalog)
