from __future__ import annotations

from pathlib import Path


def missing_snippets(path: Path, required_snippets: list[str]) -> list[str]:
    content = path.read_text(encoding="utf-8")
    return [snippet for snippet in required_snippets if snippet not in content]


def run_contract_checks(repo_root: Path) -> list[str]:
    failures: list[str] = []

    workflow_path = repo_root / ".github/workflows/backend-ci.yml"
    workflow_required = [
        "uses: astral-sh/setup-uv@v4",
        "uv sync --dev",
        "uv run python scripts/codex_checks.py",
        "uv run ruff check",
        "uv run pytest",
    ]
    missing_workflow = missing_snippets(workflow_path, workflow_required)
    if missing_workflow:
        failures.append(
            "workflow missing: " + ", ".join(f"`{snippet}`" for snippet in missing_workflow),
        )

    pyproject_path = repo_root / "backend/pyproject.toml"
    pyproject_required = [
        '"pytest==',
        '"ruff==',
    ]
    missing_pyproject = missing_snippets(pyproject_path, pyproject_required)
    if missing_pyproject:
        failures.append(
            "backend/pyproject.toml missing: " + ", ".join(f"`{snippet}`" for snippet in missing_pyproject),
        )

    agents_path = repo_root / "AGENTS.md"
    agents_required = [
        "ruff check",
        "pytest",
    ]
    missing_agents = missing_snippets(agents_path, agents_required)
    if missing_agents:
        failures.append(
            "AGENTS.md missing: " + ", ".join(f"`{snippet}`" for snippet in missing_agents),
        )

    return failures


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    failures = run_contract_checks(repo_root)
    if failures:
        print("Codex checks failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Codex checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
