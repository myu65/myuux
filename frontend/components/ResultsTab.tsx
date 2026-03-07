import { RightPanel } from "../lib/api";

export function ResultsTab({ rightPanel }: { rightPanel: RightPanel | null }) {
  return (
    <div className="text-sm space-y-3">
      {(rightPanel?.results.latest_runs ?? []).map((run) => (
        <div key={run.id} className="border rounded p-2 space-y-1">
          <div className="font-medium">{run.run_type}</div>
          <div className="text-xs text-slate-500">status: {run.status}</div>
          {run.summary ? <div className="text-xs">summary: {run.summary}</div> : null}
          {run.error_text ? <div className="text-xs text-red-700">error: {run.error_text}</div> : null}
          {(run.warnings ?? []).length > 0 ? (
            <ul className="text-xs text-amber-700 list-disc pl-4">
              {run.warnings.map((warning, index) => (
                <li key={`${run.id}-warning-${index}`}>{warning}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ))}

      {(rightPanel?.results.latest_artifacts ?? []).length > 0 ? (
        <div className="space-y-2">
          <div className="font-medium">Artifacts</div>
          {rightPanel?.results.latest_artifacts.map((artifact) => (
            <div key={artifact.id} className="border rounded p-2 text-xs space-y-1">
              <div>{artifact.title}</div>
              <div className="text-slate-500">
                {artifact.artifact_type} · {artifact.storage_backend}
              </div>
              <div className="text-slate-500 break-all">{artifact.storage_key}</div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
