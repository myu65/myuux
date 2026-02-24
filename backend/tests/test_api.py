import importlib
import os
import sys
from pathlib import Path
from types import ModuleType

from sqlmodel import Session, SQLModel


def load_main(tmp_path: Path) -> ModuleType:
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'test.db'}"
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    SQLModel.metadata.clear()
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    main.init_db()
    return main


def test_create_and_list_workspaces(tmp_path: Path) -> None:
    main = load_main(tmp_path)

    with Session(main.engine) as session:
        created = main.create_workspace(main.WorkspaceCreate(name="demo"), session)
        assert created.name == "demo"

        workspaces = main.list_workspaces(session)
        assert len(workspaces) == 1
        assert workspaces[0].name == "demo"


def test_chat_creates_run(tmp_path: Path) -> None:
    main = load_main(tmp_path)

    with Session(main.engine) as session:
        workspace = main.create_workspace(main.WorkspaceCreate(name="demo"), session)

        body = main.chat_trigger(
            workspace.id,
            main.ChatCreate(prompt="revise this", skill="ppt_revise"),
            session,
        )

        assert "message_id" in body
        assert "run_id" in body


def test_feature_catalog_lists_extension_points(tmp_path: Path) -> None:
    main = load_main(tmp_path)

    body = main.get_feature_catalog()
    assert body.version == "1.0"
    assert "run_creation" in body.extension_points
    assert "artifact_upload" in body.extension_points
