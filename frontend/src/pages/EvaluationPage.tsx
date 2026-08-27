import { useEffect, useState } from "react";
import { FlaskConical, Loader2, Plus, Play, Trash2 } from "lucide-react";
import toast from "react-hot-toast";
import { kbApi, evalApi } from "../api/endpoints";
import type { KnowledgeBase } from "../types";
import { extractErrorMessage } from "../api/client";

const METRICS = [
  { key: "retrieval_recall", label: "Retrieval recall" },
  { key: "context_precision", label: "Context precision" },
  { key: "answer_faithfulness", label: "Answer faithfulness" },
  { key: "citation_accuracy", label: "Citation accuracy" },
  { key: "answer_relevance", label: "Answer relevance" },
  { key: "unanswerable_detection", label: "Unanswerable detection" },
];

export default function EvaluationPage() {
  const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
  const [kbId, setKbId] = useState("");
  const [questions, setQuestions] = useState<any[]>([]);
  const [runs, setRuns] = useState<any[]>([]);
  const [running, setRunning] = useState(false);

  const [showForm, setShowForm] = useState(false);
  const [q, setQ] = useState("");
  const [expectedDoc, setExpectedDoc] = useState("");
  const [expectedPage, setExpectedPage] = useState("");
  const [isAnswerable, setIsAnswerable] = useState(true);

  useEffect(() => {
    kbApi.list().then((res) => {
      setKbs(res.data);
      if (res.data.length) setKbId(res.data[0].id);
    });
  }, []);

  function loadKbData(id: string) {
    evalApi.listQuestions(id).then((res) => setQuestions(res.data));
    evalApi.runs(id).then((res) => setRuns(res.data));
  }

  useEffect(() => {
    if (kbId) loadKbData(kbId);
  }, [kbId]);

  async function addQuestion(e: React.FormEvent) {
    e.preventDefault();
    try {
      await evalApi.addQuestion(kbId, {
        knowledge_base_id: kbId,
        question: q,
        expected_document: expectedDoc,
        expected_page: expectedPage ? parseInt(expectedPage) : 0,
        is_answerable: isAnswerable,
      });
      setQ("");
      setExpectedDoc("");
      setExpectedPage("");
      setShowForm(false);
      loadKbData(kbId);
      toast.success("Question added to evaluation set");
    } catch (err) {
      toast.error(extractErrorMessage(err));
    }
  }

  async function runEval(config: Record<string, any> = {}) {
    setRunning(true);
    try {
      await evalApi.run(kbId, config);
      loadKbData(kbId);
      toast.success("Evaluation run complete");
    } catch (err) {
      toast.error(extractErrorMessage(err));
    } finally {
      setRunning(false);
    }
  }

  async function deleteQuestion(qId: string) {
    try {
      await evalApi.deleteQuestion(kbId, qId);
      loadKbData(kbId);
    } catch (err) {
      toast.error(extractErrorMessage(err));
    }
  }

  const latestRun = runs[0];

  return (
    <div className="p-8 max-w-6xl">
      <div className="flex items-center gap-2 mb-1">
        <FlaskConical size={20} className="text-amber-500" />
        <h1 className="font-display text-3xl font-semibold text-ink-900 dark:text-ink-50">Evaluation</h1>
      </div>
      <p className="text-sm text-ink-400 mb-6">Measure retrieval and generation quality against a hand-labeled question set.</p>

      <select
        value={kbId}
        onChange={(e) => setKbId(e.target.value)}
        className="px-3 py-2 mb-8 rounded-lg border border-ink-200 dark:border-ink-700 bg-ink-50 dark:bg-ink-800 text-sm outline-none"
      >
        {kbs.map((kb) => (
          <option key={kb.id} value={kb.id}>
            {kb.name}
          </option>
        ))}
      </select>

      {latestRun && (
        <div className="grid md:grid-cols-3 gap-4 mb-8">
          {METRICS.map((m) => (
            <div key={m.key} className="rounded-xl border border-ink-200 dark:border-ink-800 bg-white dark:bg-ink-900 p-4">
              <p className="font-mono text-2xl font-semibold text-teal-600 dark:text-teal-400">
                {(latestRun[m.key] * 100).toFixed(0)}%
              </p>
              <p className="text-xs text-ink-400 mt-0.5">{m.label}</p>
            </div>
          ))}
          <div className="rounded-xl border border-ink-200 dark:border-ink-800 bg-white dark:bg-ink-900 p-4 md:col-span-3">
            <p className="text-xs text-ink-400">
              {latestRun.questions_tested} questions tested · avg latency {latestRun.avg_latency_ms}ms · run at{" "}
              {new Date(latestRun.created_at).toLocaleString()}
            </p>
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <div className="rounded-xl border border-ink-200 dark:border-ink-800 bg-white dark:bg-ink-900 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-sm">Evaluation questions ({questions.length})</h3>
            <button onClick={() => setShowForm(!showForm)} className="text-ink-400 hover:text-amber-500">
              <Plus size={16} />
            </button>
          </div>

          {showForm && (
            <form onSubmit={addQuestion} className="space-y-2 mb-4 border-b border-ink-100 dark:border-ink-800 pb-4">
              <input
                required
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Question"
                className="w-full px-3 py-1.5 rounded-lg border border-ink-200 dark:border-ink-700 bg-ink-50 dark:bg-ink-800 text-sm outline-none"
              />
              <div className="flex gap-2">
                <input
                  value={expectedDoc}
                  onChange={(e) => setExpectedDoc(e.target.value)}
                  placeholder="Expected document filename"
                  className="flex-1 px-3 py-1.5 rounded-lg border border-ink-200 dark:border-ink-700 bg-ink-50 dark:bg-ink-800 text-sm outline-none"
                />
                <input
                  value={expectedPage}
                  onChange={(e) => setExpectedPage(e.target.value)}
                  placeholder="Page"
                  type="number"
                  className="w-20 px-3 py-1.5 rounded-lg border border-ink-200 dark:border-ink-700 bg-ink-50 dark:bg-ink-800 text-sm outline-none"
                />
              </div>
              <label className="flex items-center gap-2 text-xs text-ink-500">
                <input type="checkbox" checked={isAnswerable} onChange={(e) => setIsAnswerable(e.target.checked)} className="accent-amber-500" />
                This question is answerable from the documents
              </label>
              <button type="submit" className="text-sm font-medium bg-ink-100 dark:bg-ink-800 px-3 py-1.5 rounded-lg">
                Add question
              </button>
            </form>
          )}

          <ul className="space-y-2 max-h-64 overflow-y-auto">
            {questions.map((eq) => (
              <li key={eq.id} className="text-sm group flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p>{eq.question}</p>
                  <p className="text-xs text-ink-400 font-mono">
                    {eq.is_answerable ? `${eq.expected_document || "any"} p.${eq.expected_page || "-"}` : "unanswerable"}
                  </p>
                </div>
                <button
                  onClick={() => deleteQuestion(eq.id)}
                  className="text-ink-400 hover:text-rose-500 opacity-0 group-hover:opacity-100 shrink-0 mt-0.5"
                  title="Delete question"
                >
                  <Trash2 size={13} />
                </button>
              </li>
            ))}
            {questions.length === 0 && <p className="text-xs text-ink-400">No evaluation questions yet.</p>}
          </ul>
        </div>

        <div className="rounded-xl border border-ink-200 dark:border-ink-800 bg-white dark:bg-ink-900 p-5">
          <h3 className="font-semibold text-sm mb-4">Run evaluation</h3>
          <p className="text-xs text-ink-400 mb-4">
            Runs the full pipeline against every question above and computes real metrics — nothing here is fabricated.
          </p>
          <div className="space-y-2">
            <button
              onClick={() => runEval({})}
              disabled={running || questions.length === 0}
              className="w-full flex items-center justify-center gap-2 bg-ink-900 dark:bg-amber-500 text-white dark:text-ink-950 text-sm font-medium py-2.5 rounded-lg hover:opacity-90 disabled:opacity-60"
            >
              {running ? <Loader2 size={15} className="animate-spin" /> : <Play size={15} />}
              Run with current config
            </button>
            <button
              onClick={() => runEval({ hybrid: false, reranker: false })}
              disabled={running || questions.length === 0}
              className="w-full text-sm font-medium border border-ink-200 dark:border-ink-700 py-2.5 rounded-lg hover:bg-ink-100 dark:hover:bg-ink-800 disabled:opacity-60"
            >
              Run: vector-only, no reranker (baseline)
            </button>
          </div>

          {runs.length > 0 && (
            <div className="mt-5 pt-4 border-t border-ink-100 dark:border-ink-800">
              <p className="text-xs font-medium text-ink-500 mb-2">Run history</p>
              <ul className="space-y-1 text-xs font-mono text-ink-400">
                {runs.slice(0, 5).map((r) => (
                  <li key={r.id}>
                    {new Date(r.created_at).toLocaleString()} — recall {(r.retrieval_recall * 100).toFixed(0)}%, faithfulness{" "}
                    {(r.answer_faithfulness * 100).toFixed(0)}%
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}