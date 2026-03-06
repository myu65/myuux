export const apiBase = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export function createUrl(path: string): string {
  return `${apiBase}${path}`;
}

export type Conversation = {
  id: string;
  title: string;
  selected_leaf_message_id?: string | null;
};

export type PathMessage = {
  id: string;
  parent_message_id?: string | null;
  role: string;
  text: string;
};

export type ConversationDetail = {
  id: string;
  title: string;
  selected_leaf_message_id?: string | null;
  selected_path_messages: PathMessage[];
};

export type FileItem = {
  id: string;
  conversation_id: string;
  filename: string;
  included_in_context: boolean;
  storage_backend: string;
  storage_key: string;
  mime_type?: string | null;
  size_bytes?: number | null;
};

export type RightPanel = {
  results: {
    latest_runs: Array<{
      id: string;
      run_type: string;
      status: string;
      summary?: string | null;
      error_text?: string | null;
      warnings: string[];
    }>;
    latest_artifacts: Array<{
      id: string;
      title: string;
      artifact_type: string;
      storage_key: string;
      storage_backend: string;
      metadata: Record<string, unknown>;
    }>;
  };
  files: FileItem[];
  summaries: {
    conversation_summary?: string | null;
    branch_summary?: string | null;
    latest_file_summary?: string | null;
  };
  agent: {
    model: string;
    store: boolean;
  };
};

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(createUrl(path));
  if (!response.ok) {
    throw new Error(`GET ${path} failed`);
  }
  return (await response.json()) as T;
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(createUrl(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    throw new Error(`POST ${path} failed`);
  }
  return (await response.json()) as T;
}
