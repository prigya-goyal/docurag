import { useState } from "react";
import { Search as SearchIcon, Loader2 } from "lucide-react";
import { searchApi } from "../api/endpoints";

export default function SearchTab({ kbId }: { kbId: string }) {
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[] | null>(null);

  async function runSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;
    setLoading(true);
    try {
      const res = await searchApi.search(kbId, q);
      setResults(res.data.results);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl">
      <form onSubmit={runSearch} className="flex gap-2 mb-6">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search chunks by keyword or concept (hybrid vector + BM25)…"
          className="flex-1 px-3 py-2.5 rounded-lg border border-ink-200 dark:border-ink-700 bg-ink-50 dark:bg-ink-800 text-sm outline-none focus:ring-2 focus:ring-amber-500/50"
        />
        <button
          type="submit"
          disabled={loading}
          className="flex items-center gap-2 bg-ink-900 dark:bg-amber-500 text-white dark:text-ink-950 text-sm font-medium px-4 py-2.5 rounded-lg hover:opacity-90"
        >
          {loading ? <Loader2 size={15} className="animate-spin" /> : <SearchIcon size={15} />}
        </button>
      </form>

      {results && (
        <div className="space-y-3">
          {results.length === 0 && <p className="text-sm text-ink-400">No matches found.</p>}
          {results.map((r) => (
            <div key={r.chunk_id} className="rounded-xl border border-ink-200 dark:border-ink-800 bg-white dark:bg-ink-900 p-4">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-medium text-ink-500">
                  {r.filename} · page {r.page_number}
                </p>
                <div className="flex gap-2 font-mono text-[10px] text-ink-400">
                  <span title="Vector similarity">V {r.vector_score.toFixed(2)}</span>
                  <span title="BM25 keyword score">K {r.bm25_score.toFixed(2)}</span>
                  <span className="text-amber-600 dark:text-amber-400" title="Hybrid score">
                    H {r.hybrid_score.toFixed(2)}
                  </span>
                </div>
              </div>
              <p className="text-sm text-ink-600 dark:text-ink-300 leading-relaxed">{r.text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
