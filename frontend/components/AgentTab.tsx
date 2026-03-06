import { RightPanel } from "../lib/api";

export function AgentTab({ rightPanel }: { rightPanel: RightPanel | null }) {
  return (
    <div className="text-sm">
      <div>model: {rightPanel?.agent.model ?? "-"}</div>
      <div>store: {String(rightPanel?.agent.store ?? false)}</div>
    </div>
  );
}
