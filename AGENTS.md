## Project Goal
Artifact-first Workspace web UI for agent-generated files (PPT/PDF/XLSX/etc).

## Core Principles
- Not a full IDE
- Artifact preview is the main UX
- raw is immutable
- outputs go to out
- publish is explicit
- runs are traceable and reproducible

## Coding Style
- Small functions
- Clear API contracts
- Prefer typed schemas
- Add docs when adding endpoints

## Quality Gate (追加)
- テスト駆動開発（TDD）を基本にする
  - 変更前に失敗するテストを書く（Red）
  - 最小実装で通す（Green）
  - リファクタリングして可読性を上げる（Refactor）
- PR前に最低限以下を通す
  - `ruff check`
  - `pytest`

## MVP Priority
1. Preview
2. Run logs (SSE)
3. Chat-triggered runs
4. Versioning
5. Real PPTX/PDF/XLSX preview
