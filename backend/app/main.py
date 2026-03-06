from app.api.conversations import (
    branch_from_message,
    create_conversation,
    create_conversation_message,
    get_conversation,
    list_conversations,
    regenerate_message,
)
from app.api.conversations import (
    register_routes as register_conversation_routes,
)
from app.api.files import (
    create_upload_url,
    exclude_file,
    get_conversation_right_panel,
    include_file,
    list_conversation_files,
    register_file,
    summarize_file,
)
from app.api.files import (
    register_routes as register_file_routes,
)
from app.api.runs import (
    list_conversation_artifacts,
    list_conversation_runs,
)
from app.api.runs import (
    register_routes as register_run_routes,
)
from app.api.workspaces import (
    chat_trigger,
    complete_run,
    create_run,
    create_workspace,
    get_artifact_version_chain,
    get_feature_catalog,
    get_run,
    get_workspace,
    list_artifacts,
    list_runs,
    list_workspaces,
    publish_artifact,
    run_events,
    upload_file,
)
from app.api.workspaces import (
    register_routes as register_workspace_routes,
)
from app.db import engine, init_db
from app.models import Artifact, Conversation, ConversationMessage, FileRecord, Workspace
from app.schemas import (
    BranchCreate,
    ChatCreate,
    ConversationCreate,
    ConversationMessageCreate,
    FileRegisterCreate,
    RunComplete,
    RunCreate,
    WorkspaceCreate,
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Artifact-first Workspace API", version="0.3.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)
register_workspace_routes(app)
register_conversation_routes(app)
register_file_routes(app)
register_run_routes(app)


@app.on_event("startup")
def startup() -> None:
    init_db()


__all__ = [
    "app",
    "engine",
    "init_db",
    "Workspace",
    "Artifact",
    "Conversation",
    "ConversationMessage",
    "FileRecord",
    "WorkspaceCreate",
    "RunCreate",
    "RunComplete",
    "ChatCreate",
    "ConversationCreate",
    "ConversationMessageCreate",
    "BranchCreate",
    "FileRegisterCreate",
    "create_workspace",
    "list_workspaces",
    "get_workspace",
    "upload_file",
    "list_artifacts",
    "create_run",
    "complete_run",
    "publish_artifact",
    "get_artifact_version_chain",
    "list_runs",
    "get_run",
    "chat_trigger",
    "run_events",
    "get_feature_catalog",
    "list_conversations",
    "create_conversation",
    "get_conversation",
    "create_conversation_message",
    "regenerate_message",
    "branch_from_message",
    "create_upload_url",
    "register_file",
    "list_conversation_files",
    "include_file",
    "exclude_file",
    "summarize_file",
    "get_conversation_right_panel",
    "list_conversation_runs",
    "list_conversation_artifacts",
]
