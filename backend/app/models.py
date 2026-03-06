from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlmodel import Field, SQLModel


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
    published_at: Optional[datetime] = None
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


class Conversation(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    title: str
    owner_user_id: Optional[str] = None
    selected_leaf_message_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationMessage(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    conversation_id: str = Field()
    parent_message_id: Optional[str] = Field(default=None)
    role: str
    content_json: str
    status: str = "completed"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationRun(SQLModel, table=True):
    __tablename__ = "conversation_run"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    conversation_id: str = Field()
    message_id: Optional[str] = Field(default=None)
    branch_leaf_message_id: Optional[str] = None
    run_type: str
    status: str
    model_name: Optional[str] = None
    summary: Optional[str] = None
    error_text: Optional[str] = None
    warnings_json: str = "[]"
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FileRecord(SQLModel, table=True):
    __tablename__ = "file_record"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    conversation_id: str = Field()
    filename: str
    storage_backend: str
    storage_key: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    editor_type: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FileBinding(SQLModel, table=True):
    __tablename__ = "file_binding"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    conversation_id: str = Field()
    file_id: str = Field()
    branch_id: Optional[str] = None
    included_in_context: bool = False
    summary_mode: str = "none"
    indexing_mode: str = "none"
    edit_mode: str = "readonly"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FileSummary(SQLModel, table=True):
    __tablename__ = "file_summary"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    file_id: str = Field()
    conversation_id: str = Field()
    branch_id: Optional[str] = None
    summary_type: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationArtifact(SQLModel, table=True):
    __tablename__ = "conversation_artifact"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    conversation_id: str = Field()
    run_id: str = Field()
    message_id: Optional[str] = None
    file_id: Optional[str] = None
    artifact_type: str
    title: str
    storage_backend: str
    storage_key: str
    metadata_json: str = "{}"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
