import { useEffect, useState } from "react";
import { analyticsApi } from "../api/endpoints";
import { Skeleton } from "../components/Skeleton";

export default function AnalyticsPage() {
  const [data, setData] = useState<any | null>(null);

  useEffect(() => {
    analyticsApi.get().then((res) => setData(res.data));
  }, []);

  return (
    <div className="p-8 max-w-5xl">
      <h1 className="font-display text-3xl font-semibold text-ink-900 dark:text-ink-50 mb-1">Analytics</h1>
      <p className="text-sm text-ink-400 mb-8">Usage, latency, and feedback across your knowledge bases.</p>

      {!data ? (
        <div className="grid md:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-xl" />
          ))}
        </div>
      ) : (
        <>
          <div className="grid md:grid-cols-4 gap-4 mb-8">
            {[
              { label: "Questions asked", value: data.questions_asked },
              { label: "Failed questions", value: data.failed_questions },
              { label: "👍 Helpful", value: data.feedback.up },
              { label: "👎 Not helpful", value: data.feedback.down },
            ].map((s) => (
              <div key={s.label} className="rounded-xl border border-ink-200 dark:border-ink-800 bg-white dark:bg-ink-900 p-4">
                <p className="font-mono text-2xl font-semibold">{s.value}</p>
                <p className="text-xs text-ink-400 mt-0.5">{s.label}</p>
              </div>
            ))}
          </div>

          <div className="grid md:grid-cols-2 gap-4 mb-8">
            <div className="rounded-xl border border-ink-200 dark:border-ink-800 bg-white dark:bg-ink-900 p-5">
              <h3 className="font-semibold text-sm mb-4">Latency breakdown</h3>
              <div className="space-y-2 text-sm font-mono">
                <div className="flex justify-between"><span className="text-ink-400">Retrieval</span><span>{data.avg_retrieval_latency_ms} ms</span></div>
                <div className="flex justify-between"><span className="text-ink-400">Generation</span><span>{data.avg_generation_latency_ms} ms</span></div>
                <div className="flex justify-between font-semibold"><span className="text-ink-400">Total (avg)</span><span>{data.avg_total_latency_ms} ms</span></div>
              </div>
            </div>
            <div className="rounded-xl border border-ink-200 dark:border-ink-800 bg-white dark:bg-ink-900 p-5">
              <h3 className="font-semibold text-sm mb-4">Other metrics</h3>
              <div className="space-y-2 text-sm font-mono">
                <div className="flex justify-between"><span className="text-ink-400">Avg citations / answer</span><span>{data.avg_citations_per_answer}</span></div>
                <div className="flex justify-between"><span className="text-ink-400">Avg doc processing time</span><span>{data.avg_document_processing_time_ms} ms</span></div>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-ink-200 dark:border-ink-800 bg-white dark:bg-ink-900 p-5">
            <h3 className="font-semibold text-sm mb-4">Most used knowledge bases</h3>
            {data.most_used_knowledge_bases.length === 0 ? (
              <p className="text-xs text-ink-400">No questions asked yet.</p>
            ) : (
              <ul className="space-y-2">
                {data.most_used_knowledge_bases.map((kb: any) => (
                  <li key={kb.knowledge_base} className="flex justify-between text-sm">
                    <span>{kb.knowledge_base}</span>
                    <span className="font-mono text-ink-400">{kb.questions} questions</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  );
}
