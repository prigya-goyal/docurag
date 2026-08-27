import { useCallback, useEffect, useRef, useState } from "react";
import { Upload, FileText, Trash2 } from "lucide-react";
import toast from "react-hot-toast";
import { documentApi } from "../api/endpoints";
import type { DocumentItem } from "../types";
import StatusBadge, { activeStates } from "./StatusBadge";
import EmptyState from "./EmptyState";
import { extractErrorMessage } from "../api/client";

const ACCEPTED = ".pdf,.docx,.pptx,.txt,.md,.csv";

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export default function DocumentsTab({ kbId }: { kbId: string }) {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<number | null>(null);

  function load() {
    documentApi
      .list(kbId)
      .then((res) => setDocs(res.data))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kbId]);

  // Poll while any document is still processing, so uploads never block the UI
  useEffect(() => {
    const hasActive = docs.some((d) => activeStates.includes(d.status));
    if (hasActive && !pollRef.current) {
      pollRef.current = window.setInterval(load, 2000);
    } else if (!hasActive && pollRef.current) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [docs]);

  async function handleFiles(files: FileList | File[]) {
    const arr = Array.from(files);
    if (arr.length === 0) return;
    setUploading(true);
    try {
      await documentApi.upload(kbId, arr);
      toast.success(`${arr.length} file${arr.length > 1 ? "s" : ""} uploaded — processing in the background`);
      load();
    } catch (err) {
      toast.error(extractErrorMessage(err));
    } finally {
      setUploading(false);
    }
  }

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      handleFiles(e.dataTransfer.files);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [kbId]
  );

  async function handleDelete(docId: string) {
    try {
      await documentApi.remove(kbId, docId);
      setDocs((prev) => prev.filter((d) => d.id !== docId));
      toast.success("Document deleted");
    } catch (err) {
      toast.error(extractErrorMessage(err));
    }
  }

  return (
    <div className="space-y-6">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
          dragOver
            ? "border-amber-500 bg-amber-500/5"
            : "border-ink-300 dark:border-ink-700 hover:border-ink-400 dark:hover:border-ink-600"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ACCEPTED}
          className="hidden"
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
        />
        <Upload size={22} className="mx-auto text-ink-400 mb-2" />
        <p className="text-sm font-medium">{uploading ? "Uploading…" : "Drag & drop files, or click to browse"}</p>
        <p className="text-xs text-ink-400 mt-1">PDF, DOCX, PPTX, TXT, Markdown, CSV — up to 50MB each</p>
      </div>

      {loading ? null : docs.length === 0 ? (
        <EmptyState icon={FileText} title="No documents yet" description="Upload a file above to start building this knowledge base." />
      ) : (
        <div className="rounded-xl border border-ink-200 dark:border-ink-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-ink-100 dark:bg-ink-800/60 text-ink-400 text-xs uppercase tracking-wide">
              <tr>
                <th className="text-left px-4 py-2.5 font-medium">File</th>
                <th className="text-left px-4 py-2.5 font-medium">Status</th>
                <th className="text-left px-4 py-2.5 font-medium">Pages</th>
                <th className="text-left px-4 py-2.5 font-medium">Chunks</th>
                <th className="text-left px-4 py-2.5 font-medium">Size</th>
                <th className="px-4 py-2.5"></th>
              </tr>
            </thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.id} className="border-t border-ink-100 dark:border-ink-800">
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-2 min-w-0">
                      <FileText size={14} className="text-ink-400 shrink-0" />
                      <span className="truncate max-w-xs">{d.filename}</span>
                      {d.used_ocr && (
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-ink-100 dark:bg-ink-800 text-ink-400 shrink-0">
                          OCR
                        </span>
                      )}
                    </div>
                    {d.status === "FAILED" && d.status_detail && (
                      <p className="text-xs text-rose-500 mt-0.5">{d.status_detail}</p>
                    )}
                  </td>
                  <td className="px-4 py-2.5">
                    <StatusBadge status={d.status} progress={d.progress_pct} />
                  </td>
                  <td className="px-4 py-2.5 font-mono text-ink-500">{d.page_count || "—"}</td>
                  <td className="px-4 py-2.5 font-mono text-ink-500">{d.chunk_count || "—"}</td>
                  <td className="px-4 py-2.5 text-ink-500">{formatBytes(d.file_size_bytes)}</td>
                  <td className="px-4 py-2.5 text-right">
                    <button onClick={() => handleDelete(d.id)} className="text-ink-400 hover:text-rose-500">
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
