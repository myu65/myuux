# TODO: Branching Chat Workspace Execution Plan

最終更新: branching chat + right workbench MVP の最小実装投入後

## A. 直近完了（今回）
- [x] 3ペイン UI（左: conversations / 中央: chat / 右: workbench tabs）
- [x] 会話ツリー（`parent_message_id`）と selected leaf path 表示
- [x] `regenerate`（sibling assistant 追加）
- [x] `branch`（任意messageから別経路の user message 作成）
- [x] file register/list/include/exclude/summarize API
- [x] right-panel 集約 API（Results / Files / Summaries / Agent）
- [x] run 保存（chat/summarize_file）

## B. 次の1スプリント
- [ ] OpenAI Responses API の実呼び出し実装（`store=false` 固定）
- [ ] temp upload file の cleanup 失敗を warnings として run に残す
- [ ] `content_json` を厳密 schema で管理（json string から typed JSON に移行）
- [ ] right-panel Results に artifact 詳細を紐付け表示

## C. 品質改善
- [ ] HTTPレベルの TestClient テスト追加（現在は関数呼び出し中心）
- [ ] フロントの UI テスト追加（tabs / include toggle / branch actions）
- [ ] migration 管理導入（現状 create_all ベース）

## D. 非ゴール（当面）
- [ ] SPCS
- [ ] 高度な Office 編集UI
- [ ] マルチユーザー RBAC 本実装
- [ ] 本格RAG/Cortex Search
