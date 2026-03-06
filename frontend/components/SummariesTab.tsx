import { RightPanel } from "../lib/api";

export function SummariesTab({ rightPanel }: { rightPanel: RightPanel | null }) {
  return <pre className="text-xs">{rightPanel?.summaries.latest_file_summary ?? "no summary"}</pre>;
}
