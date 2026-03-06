import importlib
import os
import sys
from pathlib import Path
from types import ModuleType

from sqlmodel import Session, SQLModel


def load_main(tmp_path: Path) -> ModuleType:
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'branching.db'}"
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    SQLModel.metadata.clear()
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    main.init_db()
    return main


def test_conversation_message_path_and_selected_leaf(tmp_path: Path) -> None:
    main = load_main(tmp_path)

    with Session(main.engine) as session:
        conversation = main.create_conversation(main.ConversationCreate(title="spec review"), session)
        first = main.create_conversation_message(
            conversation.id,
            main.ConversationMessageCreate(text="hello"),
            session,
        )

        detail = main.get_conversation(conversation.id, session)

        assert first.user_message_id is not None
        assert first.assistant_message_id is not None
        assert detail.selected_leaf_message_id == first.assistant_message_id
        assert len(detail.selected_path_messages) >= 2


def test_regenerate_creates_sibling_assistant(tmp_path: Path) -> None:
    main = load_main(tmp_path)

    with Session(main.engine) as session:
        conversation = main.create_conversation(main.ConversationCreate(title="regenerate"), session)
        created = main.create_conversation_message(
            conversation.id,
            main.ConversationMessageCreate(text="original"),
            session,
        )

        regenerated = main.regenerate_message(created.user_message_id, session)

        assert regenerated.parent_message_id == created.user_message_id
        assert regenerated.id != created.assistant_message_id


def test_branch_creates_new_user_message(tmp_path: Path) -> None:
    main = load_main(tmp_path)

    with Session(main.engine) as session:
        conversation = main.create_conversation(main.ConversationCreate(title="branch"), session)
        created = main.create_conversation_message(
            conversation.id,
            main.ConversationMessageCreate(text="seed"),
            session,
        )

        branched = main.branch_from_message(
            created.user_message_id,
            main.BranchCreate(text="another route"),
            session,
        )

        assert branched.parent_message_id == created.user_message_id
        assert branched.role == "user"


def test_files_include_and_summary_visible_in_right_panel(tmp_path: Path) -> None:
    main = load_main(tmp_path)

    with Session(main.engine) as session:
        conversation = main.create_conversation(main.ConversationCreate(title="files"), session)
        registered = main.register_file(
            main.FileRegisterCreate(
                conversation_id=conversation.id,
                filename="spec.md",
                storage_backend="local",
                storage_key="conversations/spec.md",
                mime_type="text/markdown",
                size_bytes=123,
            ),
            session,
        )

        included = main.include_file(conversation.id, registered.id, session)
        assert included.included_in_context is True

        summary = main.summarize_file(conversation.id, registered.id, session)
        assert summary.summary_type == "short"

        right = main.get_conversation_right_panel(conversation.id, session)
        assert len(right.files) == 1
        assert right.agent["store"] is False
        assert len(right.results["latest_runs"]) >= 1
