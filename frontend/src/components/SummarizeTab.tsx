import { useEffect, useState } from "react";
import { FileDown, Loader2, HelpCircle } from "lucide-react";
import toast from "react-hot-toast";
import { documentApi, questionsApi, summarizeApi } from "../api/endpoints";
import type { DocumentItem } from "../types";
import { extractErrorMessage } from "../api/client";

const SUMMARY_MODES = [
  { value: "executive", label: "Executive summary" },
  { value: "tldr", label: "TL;DR" },
  { value: "key_points", label: "Key points" },
  { value: "explain_simply", label: "Explain simply" },
];

export default function SummarizeTab({ kbId }: { kbId: string }) {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [docId, setDocId] = useState("");
  const [mode, setMode] = useState("executive");
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<{ summary: string; strategy: string } | null>(null);

  const [qLoading, setQLoading] = useState(false);
  const [difficulty, setDifficulty] = useState("medium");
  const [questions, setQuestions] = useState<any[] | null>(null);

  useEffect(() => {
    documentApi.list(kbId).then((res) => {
      const ready = res.data.filter((d) => d.status === "COMPLETED");
      setDocs(ready);
      if (ready.length) setDocId(ready[0].id);
    });
  }, [kbId]);

  async function runSummarize() {
    if (!docId) return;
    setLoading(true);
    setSummary(null);
    try {
      const res = await summarizeApi.summarize(kbId, docId, mode);
      setSummary(res.data);
    } catch (err) {
      toast.error(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function runGenerateQuestions() {
    if (!docId) return;
    setQLoading(true);
    setQuestions(null);
    try {
      const res = await questionsApi.generate(kbId, docId, difficulty, 5);
      setQuestions(res.data.questions);
    } catch (err) {
      toast.error(extractErrorMessage(err));
    } finally {
      setQLoading(false);
    }
  }

  if (docs.length === 0) {
    return <p className="text-sm text-ink-400">No processed documents yet. Upload and wait for processing to complete.</p>;
  }

  return (
    <div className="space-y-8 max-w-3xl">
      <div className="flex items-center gap-3">
        <label className="text-xs font-medium text-ink-500">Document</label>
        <select
          value={docId}
          onChange={(e) => setDocId(e.target.value)}
          className="px-3 py-1.5 rounded-lg border border-ink-200 dark:border-ink-700 bg-ink-50 dark:bg-ink-800 text-sm outline-none"
        >
          {docs.map((d) => (
            <option key={d.id} value={d.id}>
              {d.filename}
            </option>
          ))}
        </select>
      </div>

      <section className="rounded-xl border border-ink-200 dark:border-ink-800 bg-white dark:bg-ink-900 p-5">
        <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
          <FileDown size={15} className="text-amber-500" /> Summarize
        </h3>
        <div className="flex flex-wrap gap-2 mb-4">
          {SUMMARY_MODES.map((m) => (
            <button
              key={m.value}
              onClick={() => setMode(m.value)}
              className={`text-xs px-3 py-1.5 rounded-full border ${
                mode === m.value
                  ? "bg-ink-900 dark:bg-amber-500 text-white dark:text-ink-950 border-transparent"
                  : "border-ink-200 dark:border-ink-700 text-ink-500"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
        <button
          onClick={runSummarize}
          disabled={loading}
          className="flex items-center gap-2 text-sm font-medium bg-ink-100 dark:bg-ink-800 px-4 py-2 rounded-lg hover:bg-ink-200 dark:hover:bg-ink-700 disabled:opacity-60"
        >
          {loading && <Loader2 size={14} className="animate-spin" />}
          Generate summary
        </button>
        {summary && (
          <div className="mt-4 text-sm leading-relaxed whitespace-pre-wrap border-t border-ink-100 dark:border-ink-800 pt-4">
            {summary.strategy === "map_reduce" && (
              <p className="text-xs text-ink-400 mb-2 font-mono">Used hierarchical map-reduce summarization (long document)</p>
            )}
            {summary.summary}
          </div>
        )}
      </section>

      <section className="rounded-xl border border-ink-200 dark:border-ink-800 bg-white dark:bg-ink-900 p-5">
        <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
          <HelpCircle size={15} className="text-teal-500" /> Generate questions
        </h3>
        <div className="flex flex-wrap gap-2 mb-4">
          {["easy", "medium", "hard"].map((d) => (
            <button
              key={d}
              onClick={() => setDifficulty(d)}
              className={`text-xs px-3 py-1.5 rounded-full border capitalize ${
                difficulty === d
                  ? "bg-ink-900 dark:bg-amber-500 text-white dark:text-ink-950 border-transparent"
                  : "border-ink-200 dark:border-ink-700 text-ink-500"
              }`}
            >
              {d}
            </button>
          ))}
        </div>
        <button
          onClick={runGenerateQuestions}
          disabled={qLoading}
          className="flex items-center gap-2 text-sm font-medium bg-ink-100 dark:bg-ink-800 px-4 py-2 rounded-lg hover:bg-ink-200 dark:hover:bg-ink-700 disabled:opacity-60"
        >
          {qLoading && <Loader2 size={14} className="animate-spin" />}
          Generate questions
        </button>
        {questions && (
          <ul className="mt-4 space-y-3 border-t border-ink-100 dark:border-ink-800 pt-4">
            {questions.map((q, i) => (
              <li key={i} className="text-sm">
                <p>{q.question}</p>
                <p className="text-xs text-ink-400 font-mono mt-0.5">
                  {q.citation?.filename} · page {q.citation?.page_number}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
