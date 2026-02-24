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

- `POST /api/workspaces`
- `GET /api/workspaces`
- `GET /api/workspaces/{id}`
- `POST /api/workspaces/{id}/upload`
- `GET /api/workspaces/{id}/artifacts`
- `POST /api/workspaces/{id}/runs`
- `GET /api/workspaces/{id}/runs`
- `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/events`
- `POST /api/workspaces/{id}/chat`

## Backend quality setup (TDD + Ruff)

```bash
cd backend
pip install -r requirements.txt
ruff check
pytest
```

- Add tests first (Red), implement minimum code (Green), then refactor (Refactor).
- Keep this flow for API changes and bug fixes.
