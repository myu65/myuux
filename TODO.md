# TODO: Concept Realization Plan (Artifact-first Workspace)

## 0. Foundation / Definition of Done
- [x] Define a concrete execution roadmap aligned with project concept.
- [ ] Add architecture decision records for immutable raw / explicit publish flow.
- [ ] Add reproducibility policy (run input hash, output provenance fields).

## 1. Preview-first UX (MVP Priority #1)
- [ ] Connect frontend preview pane to real artifact list API.
- [ ] Add artifact type-aware preview router (pptx/pdf/xlsx/image/text fallback).
- [ ] Add empty/loading/error UI states for preview.

## 2. Run Logs via SSE (MVP Priority #2)
- [ ] Wire frontend run console to `/api/runs/{id}/events`.
- [ ] Add reconnect + last-event-id behavior.
- [ ] Add backend event typing schema for structured logs.

## 3. Chat-triggered Runs (MVP Priority #3)
- [ ] Connect chat UI to `/api/workspaces/{id}/chat`.
- [ ] Show message-to-run linkage in UI timeline.
- [ ] Add validation for supported skill names.

## 4. Versioning / Traceability (MVP Priority #4)
- [x] Add run completion endpoint to register generated artifacts in `out/`.
- [x] Add explicit artifact publish endpoint.
- [x] Add per-version chain API (previous/next by version group).
- [ ] Persist structured `input_artifact_ids` / `output_artifact_ids` as JSON fields.

## 5. Real format preview adapters (MVP Priority #5)
- [ ] Add backend signed URL or file serving strategy for previews.
- [ ] Integrate first real PDF viewer.
- [ ] Integrate PPTX rendering strategy.
- [ ] Integrate XLSX grid preview strategy.

## 6. Quality / CI
- [x] Follow TDD for introduced backend APIs (Red -> Green).
- [ ] Extend tests for HTTP-level endpoint behavior with TestClient.
- [ ] Add frontend smoke tests.
- [ ] Add CI steps for `ruff check` and `pytest` if missing.

## 7. Documentation
- [x] Document newly added endpoints in README.
- [ ] Expand docs with API contracts and examples.
