import { RightPanel } from "../lib/api";

export function ResultsTab({ rightPanel }: { rightPanel: RightPanel | null }) {
  return (
    <div className="text-sm space-y-2">
      {(rightPanel?.results.latest_runs ?? []).map((run) => (
        <div key={run.id} className="border rounded p-2">
          <div>{run.run_type}</div>
          <div className="text-xs text-slate-500">status: {run.status}</div>
        </div>
      ))}
    </div>
  );
}
