from datetime import datetime

from app.db import get_session
from app.models import Conversation, ConversationMessage
from app.schemas import (
    BranchCreate,
    ConversationCreate,
    ConversationDetailResponse,
    ConversationMessageCreate,
    MessageCreateResult,
)
from app.services.conversation_service import (
    build_message_path,
    create_message_with_assistant,
    to_path_view,
)
from app.services.conversation_service import (
    regenerate_message as regenerate_message_service,
)
from app.services.openai_runner import OpenAIRunner
from fastapi import Depends, HTTPException
from sqlmodel import Session, select


def list_conversations(session: Session = Depends(get_session)) -> list[Conversation]:
    return session.exec(select(Conversation).order_by(Conversation.updated_at.desc())).all()


def create_conversation(payload: ConversationCreate, session: Session = Depends(get_session)) -> Conversation:
    conversation = Conversation(title=payload.title)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


def get_conversation(conversation_id: str, session: Session = Depends(get_session)) -> ConversationDetailResponse:
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="conversation not found")
    messages = session.exec(
        select(ConversationMessage).where(ConversationMessage.conversation_id == conversation_id)
    ).all()
    selected_path: list[ConversationMessage] = []
    if conversation.selected_leaf_message_id:
        selected_path = build_message_path(
            {message.id: message for message in messages}, conversation.selected_leaf_message_id
        )
    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        selected_leaf_message_id=conversation.selected_leaf_message_id,
        selected_path_messages=[to_path_view(message) for message in selected_path],
    )


def create_conversation_message(
    conversation_id: str, payload: ConversationMessageCreate, session: Session = Depends(get_session)
) -> MessageCreateResult:
    return create_message_with_assistant(
        session,
        conversation_id=conversation_id,
        text=payload.text,
        parent_message_id=payload.parent_message_id,
        runner=OpenAIRunner(),
    )


def regenerate_message(message_id: str, session: Session = Depends(get_session)) -> ConversationMessage:
    return regenerate_message_service(session, message_id, OpenAIRunner())


def branch_from_message(
    message_id: str, payload: BranchCreate, session: Session = Depends(get_session)
) -> MessageCreateResult:
    target_message = session.get(ConversationMessage, message_id)
    if not target_message:
        raise HTTPException(status_code=404, detail="message not found")
    created = create_message_with_assistant(
        session,
        conversation_id=target_message.conversation_id,
        text=payload.text,
        parent_message_id=target_message.id,
        runner=OpenAIRunner(),
    )
    conversation = session.get(Conversation, target_message.conversation_id)
    if conversation:
        conversation.updated_at = datetime.utcnow()
        session.add(conversation)
        session.commit()
    return created


def register_routes(app):
    app.get("/api/conversations", response_model=list[Conversation])(list_conversations)
    app.post("/api/conversations", response_model=Conversation)(create_conversation)
    app.get("/api/conversations/{conversation_id}", response_model=ConversationDetailResponse)(get_conversation)
    app.post("/api/conversations/{conversation_id}/messages", response_model=MessageCreateResult)(
        create_conversation_message
    )
    app.post("/api/messages/{message_id}/regenerate", response_model=ConversationMessage)(regenerate_message)
    app.post("/api/messages/{message_id}/branch", response_model=MessageCreateResult)(branch_from_message)
