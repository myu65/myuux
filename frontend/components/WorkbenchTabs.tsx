import { FileItem, RightPanel } from "../lib/api";
import { AgentTab } from "./AgentTab";
import { FilesTab } from "./FilesTab";
import { ResultsTab } from "./ResultsTab";
import { SummariesTab } from "./SummariesTab";

export type RightPaneTab = "results" | "files" | "summaries" | "agent";

type Props = {
  tab: RightPaneTab;
  rightPanel: RightPanel | null;
  onTabChange: (tab: RightPaneTab) => void;
  fileName: string;
  onFileNameChange: (value: string) => void;
  onRegisterFile: (event: React.FormEvent<HTMLFormElement>) => void;
  onIncludeFile: (file: FileItem, include: boolean) => void;
  onSummarizeFile: (file: FileItem) => void;
};

export function WorkbenchTabs(props: Props) {
  return (
    <section className="border rounded-lg p-3 bg-white col-span-3 space-y-3">
      <h2 className="font-bold">Workbench</h2>
      <div className="flex gap-1 text-xs">
        {(["results", "files", "summaries", "agent"] as RightPaneTab[]).map((name) => (
          <button
            key={name}
            type="button"
            onClick={() => props.onTabChange(name)}
            className={`rounded px-2 py-1 ${props.tab === name ? "bg-slate-800 text-white" : "bg-slate-200"}`}
          >
            {name}
          </button>
        ))}
      </div>
      {props.tab === "results" ? <ResultsTab rightPanel={props.rightPanel} /> : null}
      {props.tab === "files" ? (
        <FilesTab
          rightPanel={props.rightPanel}
          fileName={props.fileName}
          onFileNameChange={props.onFileNameChange}
          onRegisterFile={props.onRegisterFile}
          onIncludeFile={props.onIncludeFile}
          onSummarizeFile={props.onSummarizeFile}
        />
      ) : null}
      {props.tab === "summaries" ? <SummariesTab rightPanel={props.rightPanel} /> : null}
      {props.tab === "agent" ? <AgentTab rightPanel={props.rightPanel} /> : null}
    </section>
  );
}
