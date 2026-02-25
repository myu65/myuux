from __future__ import annotations

import re
from pathlib import Path


def missing_snippets(path: Path, required_snippets: list[str]) -> list[str]:
    content = path.read_text(encoding="utf-8")
    return [snippet for snippet in required_snippets if snippet not in content]


def has_uv_command(content: str, command: str) -> bool:
    pattern = rf"^\s*-?\s*run:\s*uv\s+run\s+[^\n#]*\b{re.escape(command)}\b"
    return re.search(pattern, content, flags=re.MULTILINE) is not None


def find_existing_paths(root: Path, relative_paths: list[str]) -> list[str]:
    return [relative_path for relative_path in relative_paths if (root / relative_path).exists()]


def run_contract_checks(repo_root: Path) -> list[str]:
    failures: list[str] = []

    workflow_path = repo_root / ".github/workflows/backend-ci.yml"
    workflow_content = workflow_path.read_text(encoding="utf-8")

    workflow_required = ["setup-uv", "uv sync"]
    missing_workflow = [snippet for snippet in workflow_required if snippet not in workflow_content]
    if missing_workflow:
        failures.append("workflow missing: " + ", ".join(f"`{snippet}`" for snippet in missing_workflow))

    for command in ["ruff", "pytest"]:
        if not has_uv_command(workflow_content, command):
            failures.append(f"workflow missing: `uv run ... {command}`")

    pyproject_path = repo_root / "backend/pyproject.toml"
    pyproject_required = ['"pytest==', '"ruff==']
    missing_pyproject = missing_snippets(pyproject_path, pyproject_required)
    if missing_pyproject:
        failures.append("backend/pyproject.toml missing: " + ", ".join(f"`{snippet}`" for snippet in missing_pyproject))

    shadowing_paths = find_existing_paths(
        repo_root,
        [
            "backend/fastapi",
            "backend/pydantic.py",
            "backend/sqlmodel.py",
        ],
    )
    if shadowing_paths:
        failures.append("remove local package-shadowing stubs: " + ", ".join(f"`{path}`" for path in shadowing_paths))

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
