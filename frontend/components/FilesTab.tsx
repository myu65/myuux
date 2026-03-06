import { FileItem, RightPanel } from "../lib/api";

type Props = {
  rightPanel: RightPanel | null;
  fileName: string;
  onFileNameChange: (value: string) => void;
  onRegisterFile: (event: React.FormEvent<HTMLFormElement>) => void;
  onIncludeFile: (file: FileItem, include: boolean) => void;
  onSummarizeFile: (file: FileItem) => void;
};

export function FilesTab(props: Props) {
  return (
    <div className="space-y-2">
      <form onSubmit={props.onRegisterFile} className="flex gap-2">
        <input value={props.fileName} onChange={(event) => props.onFileNameChange(event.target.value)} className="border rounded px-2 py-1 text-sm w-full" />
        <button className="bg-slate-700 text-white rounded px-2 py-1 text-xs" type="submit">
          register
        </button>
      </form>
      <ul className="space-y-2 text-xs">
        {(props.rightPanel?.files ?? []).map((file) => (
          <li key={file.id} className="border rounded p-2">
            <div>{file.filename}</div>
            <div className="text-slate-500">{file.included_in_context ? "included" : "excluded"}</div>
            <div className="flex gap-2 mt-1">
              <button className="text-blue-700" onClick={() => props.onIncludeFile(file, !file.included_in_context)} type="button">
                {file.included_in_context ? "exclude" : "include"}
              </button>
              <button className="text-purple-700" onClick={() => props.onSummarizeFile(file)} type="button">
                summarize
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
