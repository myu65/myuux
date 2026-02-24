from datetime import datetime
from typing import Generator, Optional

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select

app = FastAPI(title="Artifact-first Workspace API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = create_engine("sqlite:///./workspace.db", echo=False)


class Workspace(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    owner_user_id: str = "demo"
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Artifact(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int
    path: str
    type: str
    version_group: str
    version_no: int
    source_run_id: Optional[int] = None
    metadata_json: str = "{}"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Run(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int
    skill_name: str
    status: str = "queued"
    prompt: str
    params_json: str = "{}"
    input_artifact_ids: str = "[]"
    output_artifact_ids: str = "[]"
    created_by: str = "demo"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int
    run_id: Optional[int] = None
    role: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WorkspaceCreate(BaseModel):
    name: str


class RunCreate(BaseModel):
    skill: str
    prompt: str
    input_artifact_ids: list[int] = []
    params: dict = {}


class ChatCreate(BaseModel):
    prompt: str
    skill: str = "ppt_revise"


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


@app.on_event("startup")
def startup() -> None:
    SQLModel.metadata.create_all(engine)


@app.post("/api/workspaces", response_model=Workspace)
def create_workspace(payload: WorkspaceCreate, session: Session = Depends(get_session)) -> Workspace:
    workspace = Workspace(name=payload.name)
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace


@app.get("/api/workspaces", response_model=list[Workspace])
def list_workspaces(session: Session = Depends(get_session)) -> list[Workspace]:
    return session.exec(select(Workspace).order_by(Workspace.created_at.desc())).all()


@app.get("/api/workspaces/{workspace_id}", response_model=Workspace)
def get_workspace(workspace_id: int, session: Session = Depends(get_session)) -> Workspace:
    workspace = session.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="workspace not found")
    return workspace


@app.post("/api/workspaces/{workspace_id}/upload")
def upload_file(workspace_id: int, file: UploadFile = File(...), session: Session = Depends(get_session)):
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


@app.get("/api/workspaces/{workspace_id}/artifacts", response_model=list[Artifact])
def list_artifacts(workspace_id: int, session: Session = Depends(get_session)) -> list[Artifact]:
    return session.exec(select(Artifact).where(Artifact.workspace_id == workspace_id)).all()


@app.post("/api/workspaces/{workspace_id}/runs", response_model=Run)
def create_run(workspace_id: int, payload: RunCreate, session: Session = Depends(get_session)) -> Run:
    run = Run(
        workspace_id=workspace_id,
        skill_name=payload.skill,
        prompt=payload.prompt,
        input_artifact_ids=str(payload.input_artifact_ids),
        params_json=str(payload.params),
        status="running",
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


@app.get("/api/workspaces/{workspace_id}/runs", response_model=list[Run])
def list_runs(workspace_id: int, session: Session = Depends(get_session)) -> list[Run]:
    return session.exec(select(Run).where(Run.workspace_id == workspace_id).order_by(Run.created_at.desc())).all()


@app.get("/api/runs/{run_id}", response_model=Run)
def get_run(run_id: int, session: Session = Depends(get_session)) -> Run:
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return run


@app.post("/api/workspaces/{workspace_id}/chat")
def chat_trigger(workspace_id: int, payload: ChatCreate, session: Session = Depends(get_session)):
    message = Message(workspace_id=workspace_id, role="user", content=payload.prompt)
    session.add(message)
    session.commit()
    run = create_run(
        workspace_id,
        RunCreate(skill=payload.skill, prompt=payload.prompt, input_artifact_ids=[], params={}),
        session,
    )
    return {"message_id": message.id, "run_id": run.id}


@app.get("/api/runs/{run_id}/events")
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
            yield f"event: log\ndata: {{\"run_id\": {run_id}, \"step\": {idx}, \"message\": \"{step}\"}}\n\n"
        yield "event: done\ndata: {\"status\": \"success\"}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
