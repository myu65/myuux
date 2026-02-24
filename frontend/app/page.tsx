"use client";

import { useEffect, useMemo, useState } from "react";

import { createUrl } from "../lib/api";

type Workspace = {
  id: number;
  name: string;
};

type Artifact = {
  id: number;
  path: string;
  type: string;
  published_at?: string | null;
};

type Run = {
  id: number;
  skill_name: string;
  status: string;
  prompt: string;
};

const paneStyle = "border rounded-lg p-3 bg-white";

export default function HomePage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<number | null>(null);
  const [workspaceName, setWorkspaceName] = useState("demo");
  const [prompt, setPrompt] = useState("表紙を改善して");
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    void loadWorkspaces();
  }, []);

  useEffect(() => {
    if (!selectedWorkspaceId) {
      return;
    }
    void loadWorkspaceData(selectedWorkspaceId);
  }, [selectedWorkspaceId]);

  const selectedWorkspace = useMemo(
    () => workspaces.find((workspace) => workspace.id === selectedWorkspaceId),
    [selectedWorkspaceId, workspaces],
  );

  async function loadWorkspaces() {
    setLoading(true);
    try {
      const response = await fetch(createUrl("/api/workspaces"));
      if (!response.ok) {
        throw new Error("workspace list fetch failed");
      }
      const body = (await response.json()) as Workspace[];
      setWorkspaces(body);
      if (!selectedWorkspaceId && body.length > 0) {
        setSelectedWorkspaceId(body[0].id);
      }
    } finally {
      setLoading(false);
    }
  }

  async function loadWorkspaceData(workspaceId: number) {
    const [artifactResponse, runResponse] = await Promise.all([
      fetch(createUrl(`/api/workspaces/${workspaceId}/artifacts`)),
      fetch(createUrl(`/api/workspaces/${workspaceId}/runs`)),
    ]);

    if (artifactResponse.ok) {
      setArtifacts((await artifactResponse.json()) as Artifact[]);
    }
    if (runResponse.ok) {
      setRuns((await runResponse.json()) as Run[]);
    }
  }

  async function handleCreateWorkspace(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!workspaceName.trim()) {
      return;
    }

    const response = await fetch(createUrl("/api/workspaces"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: workspaceName.trim() }),
    });

    if (!response.ok) {
      return;
    }

    const created = (await response.json()) as Workspace;
    setWorkspaceName("");
    setWorkspaces((prev) => [created, ...prev]);
    setSelectedWorkspaceId(created.id);
  }

  async function handleChatSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedWorkspaceId || !prompt.trim()) {
      return;
    }

    setLogs(["run starting..."]);

    const response = await fetch(createUrl(`/api/workspaces/${selectedWorkspaceId}/chat`), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: prompt.trim(), skill: "ppt_revise" }),
    });

    if (!response.ok) {
      setLogs(["failed to start run"]);
      return;
    }

    const body = (await response.json()) as { run_id: number };
    await streamRunEvents(body.run_id);
    await loadWorkspaceData(selectedWorkspaceId);
  }

  async function streamRunEvents(runId: number) {
    const response = await fetch(createUrl(`/api/runs/${runId}/events`));
    if (!response.ok || !response.body) {
      setLogs((prev) => [...prev, "failed to connect event stream"]);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() ?? "";

      for (const chunk of chunks) {
        const dataLine = chunk.split("\n").find((line) => line.startsWith("data:"));
        if (!dataLine) {
          continue;
        }
        setLogs((prev) => [...prev, dataLine.replace("data:", "").trim()]);
      }
    }
  }

  return (
    <main className="min-h-screen bg-slate-100 p-4 grid grid-cols-12 grid-rows-[1fr_220px] gap-3">
      <section className={`${paneStyle} col-span-3 row-span-1 space-y-3`}>
        <h2 className="font-bold">Workspace</h2>
        <form onSubmit={handleCreateWorkspace} className="flex gap-2">
          <input
            value={workspaceName}
            onChange={(event) => setWorkspaceName(event.target.value)}
            className="border rounded px-2 py-1 text-sm w-full"
            placeholder="new workspace"
          />
          <button className="bg-slate-800 text-white rounded px-3 py-1 text-sm" type="submit">
            Add
          </button>
        </form>

        <div className="text-xs text-slate-500">{loading ? "Loading..." : `${workspaces.length} workspace(s)`}</div>
        <ul className="space-y-2 text-sm">
          {workspaces.map((workspace) => (
            <li key={workspace.id}>
              <button
                className={`w-full text-left rounded px-2 py-1 ${
                  workspace.id === selectedWorkspaceId ? "bg-slate-200" : "hover:bg-slate-50"
                }`}
                onClick={() => setSelectedWorkspaceId(workspace.id)}
              >
                #{workspace.id} {workspace.name}
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className={`${paneStyle} col-span-6 row-span-1`}>
        <h2 className="font-bold mb-2">Artifact Preview</h2>
        <p className="text-sm mb-3">{selectedWorkspace ? `${selectedWorkspace.name} の成果物` : "ワークスペースを選択"}</p>
        <ul className="space-y-2 text-sm">
          {artifacts.length === 0 ? <li className="text-slate-500">成果物はまだありません</li> : null}
          {artifacts.map((artifact) => (
            <li key={artifact.id} className="border rounded px-2 py-1">
              <div>{artifact.path}</div>
              <div className="text-xs text-slate-500">
                type: {artifact.type} / {artifact.published_at ? "published" : "draft"}
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className={`${paneStyle} col-span-3 row-span-1`}>
        <h2 className="font-bold mb-2">AI Chat</h2>
        <form onSubmit={handleChatSubmit} className="space-y-2">
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            className="border rounded px-2 py-1 text-sm w-full h-28"
          />
          <button className="bg-blue-700 text-white rounded px-3 py-1 text-sm w-full" type="submit">
            Run via Chat
          </button>
        </form>
        <p className="text-xs text-slate-500 mt-3">runs: {runs.length}</p>
      </section>

      <section className={`${paneStyle} col-span-12 row-span-1`}>
        <h2 className="font-bold mb-2">Run Console</h2>
        <pre className="text-xs bg-slate-950 text-green-200 rounded p-3 h-40 overflow-y-auto">{logs.join("\n")}</pre>
      </section>
    </main>
  );
}
