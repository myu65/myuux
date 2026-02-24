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
    assert body.version == "1.1"
    assert "run_creation" in body.extension_points
    assert "artifact_upload" in body.extension_points


def test_complete_run_creates_output_artifact(tmp_path: Path) -> None:
    main = load_main(tmp_path)

    with Session(main.engine) as session:
        workspace = main.create_workspace(main.WorkspaceCreate(name="demo"), session)
        run = main.create_run(
            workspace.id,
            main.RunCreate(skill="ppt_revise", prompt="make v2", input_artifact_ids=[], params={}),
            session,
        )

        result = main.complete_run(
            run.id,
            main.RunComplete(output_filename="proposal_v2.pptx", artifact_type="pptx"),
            session,
        )

        assert result.status == "success"
        assert result.output_artifact.path == "out/proposal_v2.pptx"
        assert result.output_artifact.source_run_id == run.id


def test_publish_artifact_marks_published_timestamp(tmp_path: Path) -> None:
    main = load_main(tmp_path)

    with Session(main.engine) as session:
        workspace = main.create_workspace(main.WorkspaceCreate(name="demo"), session)
        artifact = main.Artifact(
            workspace_id=workspace.id,
            path="out/draft.pptx",
            type="pptx",
            version_group="draft.pptx",
            version_no=1,
        )
        session.add(artifact)
        session.commit()
        session.refresh(artifact)

        published = main.publish_artifact(artifact.id, session)

        assert published.published_at is not None


def test_get_artifact_version_chain(tmp_path: Path) -> None:
    main = load_main(tmp_path)

    with Session(main.engine) as session:
        workspace = main.create_workspace(main.WorkspaceCreate(name="demo"), session)
        v1 = main.Artifact(
            workspace_id=workspace.id,
            path="out/proposal_v1.pptx",
            type="pptx",
            version_group="proposal.pptx",
            version_no=1,
        )
        v2 = main.Artifact(
            workspace_id=workspace.id,
            path="out/proposal_v2.pptx",
            type="pptx",
            version_group="proposal.pptx",
            version_no=2,
        )
        v3 = main.Artifact(
            workspace_id=workspace.id,
            path="out/proposal_v3.pptx",
            type="pptx",
            version_group="proposal.pptx",
            version_no=3,
        )
        session.add(v1)
        session.add(v2)
        session.add(v3)
        session.commit()
        session.refresh(v2)

        chain = main.get_artifact_version_chain(v2.id, session)

        assert chain.artifact.id == v2.id
        assert chain.previous_artifact is not None
        assert chain.previous_artifact.id == v1.id
        assert chain.next_artifact is not None
        assert chain.next_artifact.id == v3.id
