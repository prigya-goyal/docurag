import clsx from "clsx";
import { ShieldCheck, ShieldAlert, ShieldQuestion } from "lucide-react";

const config = {
  HIGH: { icon: ShieldCheck, classes: "bg-teal-500/15 text-teal-600 dark:text-teal-400 border-teal-500/30" },
  MEDIUM: { icon: ShieldQuestion, classes: "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30" },
  LOW: { icon: ShieldAlert, classes: "bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30" },
};

export default function GroundingBadge({ label, score }: { label: string; score?: number }) {
  const c = config[label as keyof typeof config] ?? config.LOW;
  const Icon = c.icon;
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold border font-mono",
        c.classes
      )}
      title={score !== undefined ? `Grounding score: ${score.toFixed(2)}` : undefined}
    >
      <Icon size={12} />
      {label}
    </span>
  );
}
