# Artifact-first Workspace MVP Blueprint

## コンセプト
IDEではなく成果物中心のワークスペースを提供し、AIチャットを Run 起動トリガとして扱う。

## 画面構成
- 左: Files / Runs / Versions
- 中央: Artifact Preview
- 右: AI Chat + Skill selector
- 下: Run Console (SSE streaming)

## MVPスコープ
1. FastAPI: Workspace CRUD, upload, run create, run list/detail, artifact list, SSE logs
2. Next.js: 4-pane UI shell + workspace/runs/artifacts表示 + chat送信
3. Postgres: Workspace / Artifact / Run / Message の最小スキーマ

## ディレクトリ
- `backend/`: FastAPI API
- `frontend/`: Next.js App Router UI
- `docs/`: 設計メモ

## 次段階
- Run worker を Redis Queue + worker process に分離
- Preview adapter を skill ごとに追加
- publish/version compare の高度化

## 追加したAPI契約（Run Traceability）
- `POST /api/runs/{run_id}/complete`
  - 目的: Run完了時に `out/` への成果物登録を行い、runとartifactの因果を残す。
  - 入力: `output_filename`, `artifact_type`
  - 出力: `run_id`, `status`, `output_artifact`
- `POST /api/artifacts/{artifact_id}/publish`
  - 目的: publishを明示的な操作として記録する。
  - 出力: `published_at` が設定された Artifact
