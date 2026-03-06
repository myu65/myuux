"use client";

import { useEffect, useMemo, useState } from "react";

import { apiGet, apiPost, Conversation, ConversationDetail, FileItem, RightPanel } from "../lib/api";

type RightPaneTab = "results" | "files" | "summaries" | "agent";

const paneStyle = "border rounded-lg p-3 bg-white";

export default function HomePage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ConversationDetail | null>(null);
  const [rightPanel, setRightPanel] = useState<RightPanel | null>(null);
  const [tab, setTab] = useState<RightPaneTab>("results");
  const [newConversationTitle, setNewConversationTitle] = useState("MVP chat");
  const [messageText, setMessageText] = useState("この仕様書を要約して");
  const [fileName, setFileName] = useState("spec.md");
  const [loading, setLoading] = useState(false);

  const selectedConversation = useMemo(
    () => conversations.find((conversation) => conversation.id === selectedConversationId),
    [conversations, selectedConversationId],
  );

  useEffect(() => {
    void loadConversations();
  }, []);

  useEffect(() => {
    if (!selectedConversationId) {
      return;
    }
    void loadConversationBundle(selectedConversationId);
  }, [selectedConversationId]);

  async function loadConversations() {
    setLoading(true);
    try {
      const list = await apiGet<Conversation[]>("/api/conversations");
      setConversations(list);
      if (!selectedConversationId && list.length > 0) {
        setSelectedConversationId(list[0].id);
      }
    } finally {
      setLoading(false);
    }
  }

  async function loadConversationBundle(conversationId: string) {
    const [conversationDetail, panel] = await Promise.all([
      apiGet<ConversationDetail>(`/api/conversations/${conversationId}`),
      apiGet<RightPanel>(`/api/conversations/${conversationId}/right-panel`),
    ]);
    setDetail(conversationDetail);
    setRightPanel(panel);
  }

  async function handleCreateConversation(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!newConversationTitle.trim()) {
      return;
    }
    const created = await apiPost<Conversation>("/api/conversations", {
      title: newConversationTitle.trim(),
    });
    setConversations((prev) => [created, ...prev]);
    setSelectedConversationId(created.id);
    setNewConversationTitle("");
  }

  async function handleSendMessage(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedConversationId || !messageText.trim()) {
      return;
    }
    await apiPost(`/api/conversations/${selectedConversationId}/messages`, {
      text: messageText.trim(),
      parent_message_id: detail?.selected_leaf_message_id ?? undefined,
    });
    await loadConversationBundle(selectedConversationId);
  }

  async function handleRegenerate(messageId: string) {
    await apiPost(`/api/messages/${messageId}/regenerate`);
    if (selectedConversationId) {
      await loadConversationBundle(selectedConversationId);
    }
  }

  async function handleBranch(messageId: string) {
    await apiPost(`/api/messages/${messageId}/branch`, {
      text: "別案として考えて",
    });
    if (selectedConversationId) {
      await loadConversationBundle(selectedConversationId);
    }
  }

  async function handleRegisterFile(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedConversationId || !fileName.trim()) {
      return;
    }
    await apiPost("/api/files/register", {
      conversation_id: selectedConversationId,
      filename: fileName.trim(),
      storage_backend: "local",
      storage_key: `conversations/${selectedConversationId}/${fileName.trim()}`,
      mime_type: "text/markdown",
      size_bytes: 100,
    });
    await loadConversationBundle(selectedConversationId);
  }

  async function includeFile(file: FileItem, include: boolean) {
    if (!selectedConversationId) {
      return;
    }
    const action = include ? "include" : "exclude";
    await apiPost(`/api/conversations/${selectedConversationId}/files/${file.id}/${action}`);
    await loadConversationBundle(selectedConversationId);
  }

  async function summarizeFile(file: FileItem) {
    if (!selectedConversationId) {
      return;
    }
    await apiPost(`/api/conversations/${selectedConversationId}/files/${file.id}/summarize`);
    await loadConversationBundle(selectedConversationId);
  }

  return (
    <main className="min-h-screen bg-slate-100 p-4 grid grid-cols-12 gap-3">
      <section className={`${paneStyle} col-span-3 space-y-3`}>
        <h2 className="font-bold">Conversations</h2>
        <form onSubmit={handleCreateConversation} className="flex gap-2">
          <input
            value={newConversationTitle}
            onChange={(event) => setNewConversationTitle(event.target.value)}
            className="border rounded px-2 py-1 text-sm w-full"
            placeholder="new conversation"
          />
          <button className="bg-slate-800 text-white rounded px-3 py-1 text-sm" type="submit">
            Add
          </button>
        </form>
        <div className="text-xs text-slate-500">{loading ? "Loading..." : `${conversations.length} conversation(s)`}</div>
        <ul className="space-y-2 text-sm">
          {conversations.map((conversation) => (
            <li key={conversation.id}>
              <button
                className={`w-full text-left rounded px-2 py-1 ${
                  conversation.id === selectedConversationId ? "bg-slate-200" : "hover:bg-slate-50"
                }`}
                onClick={() => setSelectedConversationId(conversation.id)}
              >
                {conversation.title}
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className={`${paneStyle} col-span-6 space-y-3`}>
        <h2 className="font-bold">Chat</h2>
        <p className="text-sm text-slate-600">{selectedConversation ? selectedConversation.title : "会話を選択"}</p>
        <ul className="space-y-2 text-sm max-h-[70vh] overflow-y-auto">
          {detail?.selected_path_messages.map((message) => (
            <li key={message.id} className="border rounded p-2 bg-slate-50">
              <div className="font-semibold text-xs uppercase text-slate-500">{message.role}</div>
              <div>{message.text}</div>
              {message.role === "user" ? (
                <button
                  className="text-xs text-blue-700 mt-2 mr-2"
                  onClick={() => handleRegenerate(message.id)}
                  type="button"
                >
                  regenerate
                </button>
              ) : null}
              <button className="text-xs text-purple-700 mt-2" onClick={() => handleBranch(message.id)} type="button">
                branch from here
              </button>
            </li>
          ))}
        </ul>
        <form onSubmit={handleSendMessage} className="space-y-2">
          <textarea
            value={messageText}
            onChange={(event) => setMessageText(event.target.value)}
            className="border rounded px-2 py-1 text-sm w-full h-28"
          />
          <button className="bg-blue-700 text-white rounded px-3 py-1 text-sm w-full" type="submit">
            Send
          </button>
        </form>
      </section>

      <section className={`${paneStyle} col-span-3 space-y-3`}>
        <h2 className="font-bold">Workbench</h2>
        <div className="flex gap-1 text-xs">
          {(["results", "files", "summaries", "agent"] as RightPaneTab[]).map((name) => (
            <button
              key={name}
              type="button"
              onClick={() => setTab(name)}
              className={`rounded px-2 py-1 ${tab === name ? "bg-slate-800 text-white" : "bg-slate-200"}`}
            >
              {name}
            </button>
          ))}
        </div>

        {tab === "results" ? (
          <div className="text-sm space-y-2">
            {(rightPanel?.results.latest_runs ?? []).map((run) => (
              <div key={run.id} className="border rounded p-2">
                <div>{run.run_type}</div>
                <div className="text-xs text-slate-500">status: {run.status}</div>
              </div>
            ))}
          </div>
        ) : null}

        {tab === "files" ? (
          <div className="space-y-2">
            <form onSubmit={handleRegisterFile} className="flex gap-2">
              <input
                value={fileName}
                onChange={(event) => setFileName(event.target.value)}
                className="border rounded px-2 py-1 text-sm w-full"
              />
              <button className="bg-slate-700 text-white rounded px-2 py-1 text-xs" type="submit">
                register
              </button>
            </form>
            <ul className="space-y-2 text-xs">
              {(rightPanel?.files ?? []).map((file) => (
                <li key={file.id} className="border rounded p-2">
                  <div>{file.filename}</div>
                  <div className="text-slate-500">{file.included_in_context ? "included" : "excluded"}</div>
                  <div className="flex gap-2 mt-1">
                    <button
                      className="text-blue-700"
                      onClick={() => includeFile(file, !file.included_in_context)}
                      type="button"
                    >
                      {file.included_in_context ? "exclude" : "include"}
                    </button>
                    <button className="text-purple-700" onClick={() => summarizeFile(file)} type="button">
                      summarize
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {tab === "summaries" ? <pre className="text-xs">{rightPanel?.summaries.latest_file_summary ?? "no summary"}</pre> : null}

        {tab === "agent" ? (
          <div className="text-sm">
            <div>model: {rightPanel?.agent.model ?? "-"}</div>
            <div>store: {String(rightPanel?.agent.store ?? false)}</div>
          </div>
        ) : null}
      </section>
    </main>
  );
}
