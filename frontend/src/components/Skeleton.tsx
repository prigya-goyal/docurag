import clsx from "clsx";

export function Skeleton({ className }: { className?: string }) {
  return <div className={clsx("animate-pulse rounded-md bg-ink-200 dark:bg-ink-800", className)} />;
}

export function SkeletonCard() {
  return (
    <div className="rounded-xl border border-ink-200 dark:border-ink-800 p-4 space-y-3">
      <Skeleton className="h-4 w-2/3" />
      <Skeleton className="h-3 w-1/2" />
      <Skeleton className="h-3 w-1/3" />
    </div>
  );
}
