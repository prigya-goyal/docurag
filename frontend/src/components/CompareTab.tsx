import { useEffect, useState } from "react";
import { GitCompare, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import { compareApi, documentApi } from "../api/endpoints";
import type { DocumentItem } from "../types";
import { extractErrorMessage } from "../api/client";

export default function CompareTab({ kbId }: { kbId: string }) {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [focus, setFocus] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ comparison: string; citations: any[]; documents_compared: string[] } | null>(null);

  useEffect(() => {
    documentApi.list(kbId).then((res) => setDocs(res.data.filter((d) => d.status === "COMPLETED")));
  }, [kbId]);

  function toggle(id: string) {
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  async function runCompare() {
    if (selected.length < 2) {
      toast.error("Select at least 2 documents to compare");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const res = await compareApi.compare(kbId, selected, focus || undefined);
      setResult(res.data);
    } catch (err) {
      toast.error(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid md:grid-cols-[280px_1fr] gap-6">
      <div>
        <h3 className="text-sm font-semibold mb-3">Select documents</h3>
        <div className="space-y-1.5 mb-4">
          {docs.map((d) => (
            <label key={d.id} className="flex items-center gap-2 text-sm cursor-pointer px-2 py-1.5 rounded-lg hover:bg-ink-100 dark:hover:bg-ink-800">
              <input type="checkbox" checked={selected.includes(d.id)} onChange={() => toggle(d.id)} className="accent-amber-500" />
              <span className="truncate">{d.filename}</span>
            </label>
          ))}
          {docs.length === 0 && <p className="text-xs text-ink-400">No processed documents yet.</p>}
        </div>
        <label className="block text-xs font-medium text-ink-500 mb-1.5">Focus (optional)</label>
        <input
          value={focus}
          onChange={(e) => setFocus(e.target.value)}
          placeholder="e.g. What changed?"
          className="w-full px-3 py-2 rounded-lg border border-ink-200 dark:border-ink-700 bg-ink-50 dark:bg-ink-800 text-sm outline-none focus:ring-2 focus:ring-amber-500/50 mb-4"
        />
        <button
          onClick={runCompare}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 bg-ink-900 dark:bg-amber-500 text-white dark:text-ink-950 text-sm font-medium py-2.5 rounded-lg hover:opacity-90 disabled:opacity-60"
        >
          {loading ? <Loader2 size={15} className="animate-spin" /> : <GitCompare size={15} />}
          Compare
        </button>
      </div>

      <div className="rounded-xl border border-ink-200 dark:border-ink-800 bg-white dark:bg-ink-900 p-6 min-h-[300px]">
        {!result && !loading && (
          <p className="text-sm text-ink-400">Select two or more documents and run a comparison to see changes, additions, and removals.</p>
        )}
        {loading && (
          <div className="flex items-center gap-2 text-ink-400 text-sm">
            <Loader2 size={14} className="animate-spin" /> Comparing documents…
          </div>
        )}
        {result && (
          <div>
            <p className="text-xs text-ink-400 mb-3">Comparing: {result.documents_compared.join(", ")}</p>
            <div className="whitespace-pre-wrap text-sm leading-relaxed">{result.comparison}</div>
          </div>
        )}
      </div>
    </div>
  );
}
