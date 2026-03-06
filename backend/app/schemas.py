from typing import Any, Optional

from app.models import Artifact
from pydantic import BaseModel
from pydantic import Field as PydanticField


class WorkspaceCreate(BaseModel):
    name: str


class RunCreate(BaseModel):
    skill: str
    prompt: str
    input_artifact_ids: list[int] = PydanticField(default_factory=list)
    params: dict = PydanticField(default_factory=dict)


class RunComplete(BaseModel):
    output_filename: str
    artifact_type: str


class RunCompleteResponse(BaseModel):
    run_id: int
    status: str
    output_artifact: Artifact


class ArtifactVersionChain(BaseModel):
    artifact: Artifact
    previous_artifact: Artifact | None = None
    next_artifact: Artifact | None = None


class ChatCreate(BaseModel):
    prompt: str
    skill: str = "ppt_revise"


class FeatureCatalog(BaseModel):
    version: str
    extension_points: list[str]
    notes: list[str]


class ConversationCreate(BaseModel):
    title: str


class ContentPart(BaseModel):
    type: str = "text"
    text: str


class MessageContent(BaseModel):
    parts: list[ContentPart]


class ConversationMessageCreate(BaseModel):
    text: str
    parent_message_id: Optional[str] = None


class BranchCreate(BaseModel):
    text: str


class MessagePathView(BaseModel):
    id: str
    parent_message_id: Optional[str] = None
    role: str
    text: str


class MessageCreateResult(BaseModel):
    user_message_id: str
    assistant_message_id: str
    run_id: str


class ConversationDetailResponse(BaseModel):
    id: str
    title: str
    selected_leaf_message_id: Optional[str]
    selected_path_messages: list[MessagePathView]


class UploadUrlCreate(BaseModel):
    filename: str
    content_type: Optional[str] = None


class FileRegisterCreate(BaseModel):
    conversation_id: str
    filename: str
    storage_backend: str
    storage_key: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None


class FileView(BaseModel):
    id: str
    conversation_id: str
    filename: str
    storage_backend: str
    storage_key: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    included_in_context: bool = False




class RunResultView(BaseModel):
    id: str
    run_type: str
    status: str
    summary: Optional[str] = None
    error_text: Optional[str] = None
    warnings: list[str] = PydanticField(default_factory=list)


class ArtifactResultView(BaseModel):
    id: str
    title: str
    artifact_type: str
    storage_key: str
    storage_backend: str
    metadata: dict[str, Any] = PydanticField(default_factory=dict)


class RightPanelResults(BaseModel):
    latest_runs: list[RunResultView]
    latest_artifacts: list[ArtifactResultView]

class RightPanelResponse(BaseModel):
    results: RightPanelResults
    files: list[FileView]
    summaries: dict[str, Optional[str]]
    agent: dict[str, Any]
