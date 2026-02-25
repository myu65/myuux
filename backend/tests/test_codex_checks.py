import importlib.util
from pathlib import Path


def load_module():
    repo_root = Path(__file__).resolve().parents[2]
    module_path = repo_root / "backend/scripts/codex_checks.py"
    spec = importlib.util.spec_from_file_location("codex_checks", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_snippets_reports_only_missing(tmp_path: Path) -> None:
    checks = load_module()
    target = tmp_path / "target.txt"
    target.write_text("alpha\nbeta\n", encoding="utf-8")

    result = checks.missing_snippets(target, ["alpha", "beta", "gamma"])

    assert result == ["gamma"]


def test_has_uv_command_accepts_wrapped_invocation() -> None:
    checks = load_module()
    content = """
steps:
  - name: Lint
    run: uv run python -m ruff check
  - name: Test
    run: uv run python -m pytest -q
"""

    assert checks.has_uv_command(content, "ruff")
    assert checks.has_uv_command(content, "pytest")


def test_has_uv_command_rejects_non_uv_invocation() -> None:
    checks = load_module()
    content = """
steps:
  - name: Lint
    run: ruff check
"""

    assert not checks.has_uv_command(content, "ruff")


def test_find_existing_paths_reports_only_present_paths(tmp_path: Path) -> None:
    checks = load_module()
    (tmp_path / "a").mkdir()
    (tmp_path / "b.py").write_text("x", encoding="utf-8")

    existing = checks.find_existing_paths(tmp_path, ["a", "b.py", "c"])

    assert existing == ["a", "b.py"]


def test_run_contract_checks_detects_missing_contracts(tmp_path: Path) -> None:
    checks = load_module()
    (tmp_path / ".github/workflows").mkdir(parents=True)
    (tmp_path / "backend").mkdir(parents=True)
    (tmp_path / ".github/workflows/backend-ci.yml").write_text("name: Backend CI\n", encoding="utf-8")
    (tmp_path / "backend/pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")

    failures = checks.run_contract_checks(tmp_path)

    assert len(failures) == 4
    assert failures[0].startswith("workflow missing:")
    assert failures[1] == "workflow missing: `uv run ... ruff`"
    assert failures[2] == "workflow missing: `uv run ... pytest`"
    assert failures[3].startswith("backend/pyproject.toml missing:")


def test_run_contract_checks_accepts_generalized_uv_commands(tmp_path: Path) -> None:
    checks = load_module()
    (tmp_path / ".github/workflows").mkdir(parents=True)
    (tmp_path / "backend").mkdir(parents=True)
    (tmp_path / ".github/workflows/backend-ci.yml").write_text(
        """name: Backend CI
steps:
  - uses: astral-sh/setup-uv@v4
  - run: uv sync --dev
  - run: uv run python -m ruff check
  - run: uv run python -m pytest -q
""",
        encoding="utf-8",
    )
    (tmp_path / "backend/pyproject.toml").write_text(
        """[project]
name='x'

[dependency-groups]
dev = [
  \"pytest==8.3.3\",
  \"ruff==0.7.4\",
]
""",
        encoding="utf-8",
    )

    failures = checks.run_contract_checks(tmp_path)

    assert failures == []


def test_run_contract_checks_detects_shadowing_stubs(tmp_path: Path) -> None:
    checks = load_module()
    (tmp_path / ".github/workflows").mkdir(parents=True)
    (tmp_path / "backend/fastapi").mkdir(parents=True)
    (tmp_path / ".github/workflows/backend-ci.yml").write_text(
        """name: Backend CI
steps:
  - uses: astral-sh/setup-uv@v4
  - run: uv sync --dev
  - run: uv run ruff check
  - run: uv run pytest
""",
        encoding="utf-8",
    )
    (tmp_path / "backend/pyproject.toml").write_text(
        """[project]
name='x'

[dependency-groups]
dev = [
  \"pytest==8.3.3\",
  \"ruff==0.7.4\",
]
""",
        encoding="utf-8",
    )
    (tmp_path / "backend/pydantic.py").write_text("", encoding="utf-8")

    failures = checks.run_contract_checks(tmp_path)

    assert len(failures) == 1
    assert failures[0].startswith("remove local package-shadowing stubs:")
    assert "backend/fastapi" in failures[0]
    assert "backend/pydantic.py" in failures[0]
