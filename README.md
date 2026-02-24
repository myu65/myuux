# myuux
Artifact-first Workspace web ui

## MVP scaffold (Artifact-first Workspace)

- `backend/`: FastAPI API for Workspace / Artifact / Run / Chat / SSE
- `frontend/`: Next.js 4-pane shell (left files/runs, center preview, right chat, bottom logs)
- `docs/artifact-first-workspace.md`: architecture and roadmap

## Quick start

```bash
docker compose up
```

- API: http://localhost:8000/docs
- UI: http://localhost:3000

## Implemented API (MVP)

- `GET /api/features`
- `POST /api/workspaces`
- `GET /api/workspaces`
- `GET /api/workspaces/{id}`
- `POST /api/workspaces/{id}/upload`
- `GET /api/workspaces/{id}/artifacts`
- `POST /api/workspaces/{id}/runs`
- `GET /api/workspaces/{id}/runs`
- `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/events`
- `POST /api/runs/{run_id}/complete`
- `POST /api/artifacts/{artifact_id}/publish`
- `GET /api/artifacts/{artifact_id}/chain`
- `POST /api/workspaces/{id}/chat`

## Backend quality setup (TDD + Ruff)

```bash
cd backend
uv sync --dev
uv run python scripts/codex_checks.py
uv run ruff check
uv run pytest
```

- Add tests first (Red), implement minimum code (Green), then refactor (Refactor).
- Keep this flow for API changes and bug fixes.

## Concept alignment (Codex Cloud x NotebookLM style)

- Workspace is mounted and agent can operate files with a strict contract (`raw/` immutable, `out/` writable, publish explicit).
- Chat answers should be traceable to runs and artifacts (source-aware analysis).
- See `TODO.md` for prioritized gaps and decision points, and `docs/artifact-first-workspace.md` for the execution model.
- Agent foundation helpers are in `backend/app/agent_foundation.py` (run phases, skill catalog, workspace path policy).
