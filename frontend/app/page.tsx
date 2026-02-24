const paneStyle = "border rounded-lg p-3 bg-white";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-slate-100 p-4 grid grid-cols-12 grid-rows-[1fr_220px] gap-3">
      <section className={`${paneStyle} col-span-3 row-span-1`}>
        <h2 className="font-bold mb-2">Workspace</h2>
        <p className="text-sm">Files / Runs / Versions</p>
      </section>

      <section className={`${paneStyle} col-span-6 row-span-1`}>
        <h2 className="font-bold mb-2">Artifact Preview</h2>
        <p className="text-sm">PPT/PDF/XLSX/Image preview area</p>
      </section>

      <section className={`${paneStyle} col-span-3 row-span-1`}>
        <h2 className="font-bold mb-2">AI Chat</h2>
        <p className="text-sm">Generate / Revise / Convert</p>
      </section>

      <section className={`${paneStyle} col-span-12 row-span-1`}>
        <h2 className="font-bold mb-2">Run Console</h2>
        <p className="text-sm">Streaming logs and status</p>
      </section>
    </main>
  );
}
