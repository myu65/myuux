# TODO: Concept Realization Plan (Artifact-first Workspace)

最終更新: agent実装の土台まで分解（2026-02）

## A. 直近の到達点（2週間）
- [ ] ワークスペース契約を API で強制（`raw/` read-only, `out/` write-only, publish explicit）。
- [ ] Run を state machine で運用（`queued/planning/running/waiting_user/success/failed`）。
- [ ] Skill 実行契約（typed input/output）を導入。
- [ ] Run provenance（prompt hash / skill version / input-output IDs）を保存。

## B. 実装分解 TODO（優先順）

### B1. Workspace contract（基盤）
- [x] path policy helper を追加（`raw` 読み取り判定 / `out` 出力判定）。
- [ ] upload / complete API で path policy 検証を強制。
- [ ] publish 前提条件（`out` 配下のみ publish 可能）を明文化して実装。
- [ ] TestClient で不正 path の 4xx を検証。

### B2. Agent runtime contract（agent土台）
- [x] Run phase enum と遷移ルール helper を追加。
- [x] SkillSpec とデフォルト skill catalog を追加。
- [ ] run create 時に未対応 skill を 422 で拒否。
- [ ] skill version を run レコードへ保存。

### B3. Run logs / observability
- [ ] SSE event を typed 化（`state_changed`, `tool_called`, `artifact_registered`）。
- [ ] last-event-id / reconnect を実装。
- [ ] frontend console を event type 別に描画。

### B4. Reproducibility / replay
- [ ] `input_artifact_ids` / `output_artifact_ids` を JSON 構造として保存。
- [ ] provenance fields（`prompt_hash`, `model_id`, `runtime_config_json`）を追加。
- [ ] `POST /api/runs/{id}/replay` を追加。
- [ ] `GET /api/runs/{id}/provenance` を追加。

### B5. Preview-first UX
- [x] Artifact list API を preview pane に接続。
- [ ] type-aware preview router（pptx/pdf/xlsx/image/text fallback）。
- [ ] preview の loading/error/empty を分離。
- [ ] version chain compare UI。

## C. NotebookLM-like 体験（ソース根拠）
- [ ] Sources パネル（raw/out/run/message reference）を追加。
- [ ] chat 返答に artifact/run citation を付与。
- [ ] 選択 artifact 群に対する横断分析フローを追加。

## D. 品質ゲート
- [x] TDD を原則化（Red -> Green -> Refactor）。
- [ ] HTTP レベルテスト（TestClient）を拡張。
- [ ] frontend smoke test を追加。
- [x] CI に `ruff check` / `pytest` を設定。
