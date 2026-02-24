# Artifact-first Workspace MVP Blueprint

## コンセプト
IDEではなく成果物中心のワークスペースを提供し、AIチャットを Run 起動トリガとして扱う。

## 追加コンセプト（今回の要求反映）
このプロダクトは次の 2 つを同時に満たす:
1. **Codex Cloud 風**: エージェントがマウント済み workspace を実際に操作して成果物を更新する。
2. **NotebookLM 風**: ユーザーが持ち込んだソース群に基づいて、根拠付きで分析・生成する。

つまり「チャットUI + 実ファイル操作 + 根拠追跡」が成立条件。

## 画面構成
- 左: Files / Runs / Versions / Sources
- 中央: Artifact Preview（比較表示含む）
- 右: AI Chat + Skill selector + capability hints
- 下: Run Console (SSE streaming + structured events)

## MVPスコープ
1. FastAPI: Workspace CRUD, upload, run create/list/detail, artifact list, SSE logs
2. Next.js: 4-pane UI shell + workspace/runs/artifacts表示 + chat送信
3. DB: Workspace / Artifact / Run / Message の最小スキーマ

## Codex Cloud風の実行モデル（最小）
- Run state:
  - `queued`
  - `planning`
  - `running`
  - `waiting_user`（必要なら）
  - `success` / `failed`
- Agent execution rules:
  - `raw/` は immutable（上書き不可）
  - 生成物は `out/` のみ
  - publish は明示操作
- Run provenance:
  - prompt hash
  - skill name + skill version
  - input artifact version ids
  - output artifact ids
  - runtime metadata（model, temperature, etc）

## NotebookLM風の体験要件（最小）
- Sources パネルで「どの資料に基づいた回答か」を辿れる。
- Chat 返答に run / artifact への参照を持てる。
- 複数 artifact を選んで横断分析できる。

## API拡張の方向性
### すでに実装済み
- `POST /api/runs/{run_id}/complete`
- `POST /api/artifacts/{artifact_id}/publish`
- `GET /api/artifacts/{artifact_id}/chain`
- `POST /api/workspaces/{id}/chat`
- `GET /api/runs/{run_id}/events`

### 追加候補
- `GET /api/workspaces/{id}/sources`
  - Source 列挙（raw/out/message/run reference を統合）
- `POST /api/runs/{run_id}/replay`
  - 同入力での再実行
- `GET /api/runs/{run_id}/provenance`
  - 再現性情報を取得

## ディレクトリ
- `backend/`: FastAPI API
- `frontend/`: Next.js App Router UI
- `docs/`: 設計メモ

## 次段階
- Run worker を Redis Queue + worker process に分離
- Preview adapter を artifact type ごとに追加
- publish/version compare の高度化
- skill runtime contract（typed schema）を導入


## 実装済みの土台（今回追加）
- `backend/app/agent_foundation.py`
  - Run phase enum と遷移検証 (`can_transition`)
  - workspace path policy (`validate_raw_read_path`, `validate_output_path`)
  - `SkillSpec` と default skill catalog
- `backend/tests/test_agent_foundation.py`
  - phase遷移、path policy、skill catalog の単体テスト

この土台は「APIへ組み込む前の契約レイヤー」で、次のステップで `main.py` の endpoint validation に接続する。
