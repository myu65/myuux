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


def test_run_contract_checks_passes_for_current_repo() -> None:
    checks = load_module()
    repo_root = Path(__file__).resolve().parents[2]

    failures = checks.run_contract_checks(repo_root)

    assert failures == []
