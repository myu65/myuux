"use client";

import { useEffect, useMemo, useState } from "react";

import { ChatPane } from "../components/ChatPane";
import { ConversationSidebar } from "../components/ConversationSidebar";
import { RightPaneTab, WorkbenchTabs } from "../components/WorkbenchTabs";
import { apiGet, apiPost, Conversation, ConversationDetail, FileItem, RightPanel } from "../lib/api";

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
    const created = await apiPost<Conversation>("/api/conversations", { title: newConversationTitle.trim() });
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
    await apiPost(`/api/messages/${messageId}/branch`, { text: "別案として考えて" });
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
      <ConversationSidebar
        conversations={conversations}
        selectedConversationId={selectedConversationId}
        loading={loading}
        newConversationTitle={newConversationTitle}
        onNewConversationTitleChange={setNewConversationTitle}
        onCreateConversation={handleCreateConversation}
        onSelectConversation={setSelectedConversationId}
      />
      <ChatPane
        selectedConversation={selectedConversation}
        detail={detail}
        messageText={messageText}
        onMessageTextChange={setMessageText}
        onSendMessage={handleSendMessage}
        onRegenerate={handleRegenerate}
        onBranch={handleBranch}
      />
      <WorkbenchTabs
        tab={tab}
        rightPanel={rightPanel}
        onTabChange={setTab}
        fileName={fileName}
        onFileNameChange={setFileName}
        onRegisterFile={handleRegisterFile}
        onIncludeFile={includeFile}
        onSummarizeFile={summarizeFile}
      />
    </main>
  );
}
