# Artifact-first Workspace MVP Blueprint (Branching Chat + Right Workbench)

## 設計思想（更新版）
このプロダクトは **「チャット」ではなく「成果物と実行履歴」中心** の UI を維持する。

- 中央: 会話の現在枝（selected leaf までの path）
- 右: workbench（Results / Files / Summaries / Agent）
- 正本データ: DB + 自前ストレージ
- OpenAIは推論と一時利用のみ（`store=false`）

### 重要な原則
1. **Not a full IDE**
   - まずは会話/実行/ファイル設定の一貫性を優先する。
2. **Branching is first-class**
   - `parent_message_id` で会話木を表現し、`regenerate` は sibling assistant を追加する。
3. **Workspace controls context explicitly**
   - ファイルごとに `included_in_context` を持ち、会話に渡す範囲を明示する。
4. **Traceability over magic**
   - chat実行も summary実行も `runs` に残し、右ペイン Results から追跡できるようにする。

## MVP 実装スコープ（今回反映）
- Conversation API（一覧/作成/詳細）
- Message API（送信/regenerate/branch）
- File API（register/list/include/exclude/summarize）
- Right panel API（results/files/summaries/agent の集約）
- Frontend 3ペイン UI + right workbench tabs

## データモデルの方針
- `conversations.selected_leaf_message_id` で現在枝を固定
- `messages.parent_message_id` で path 再構成
- `file_bindings` で file 実体と会話利用設定を分離
- `runs` は chat/summarize を同一観測軸で記録

## 今後の拡張
- OpenAI Responses API 実呼び出しを `services/openai_runner.py` に隔離
- StorageBackend（local/s3/stage）抽象の導入
- artifact preview adapter（pptx/pdf/xlsx）
- SSE で run logs を results に統合
