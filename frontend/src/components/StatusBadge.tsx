import clsx from "clsx";
import type { ProcessingStatus } from "../types";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";

const activeStates: ProcessingStatus[] = ["UPLOADING", "PROCESSING", "OCR", "CHUNKING", "EMBEDDING", "INDEXING"];

export default function StatusBadge({ status, progress }: { status: ProcessingStatus; progress?: number }) {
  if (status === "COMPLETED") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-teal-500/15 text-teal-600 dark:text-teal-400">
        <CheckCircle2 size={12} /> Ready
      </span>
    );
  }
  if (status === "FAILED") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-rose-500/15 text-rose-600 dark:text-rose-400">
        <XCircle size={12} /> Failed
      </span>
    );
  }
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium",
        "bg-amber-500/15 text-amber-600 dark:text-amber-400"
      )}
    >
      <Loader2 size={12} className="animate-spin" />
      {status}
      {progress !== undefined ? ` · ${progress}%` : ""}
    </span>
  );
}

export { activeStates };
