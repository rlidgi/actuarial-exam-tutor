// Shape-matched loading placeholders for the useRequireAuth() gate that
// every authenticated page sits behind. Rendered in place of `return null`
// while auth/data resolves -- purely cosmetic (same real load time), but
// avoids a blank white pane during that window.

export function SkeletonBlock({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-md bg-paper-raised ${className}`} />;
}

export function ChatSkeleton() {
  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex flex-1 flex-col overflow-y-auto px-4 py-4 md:px-6">
        <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-3">
          <SkeletonBlock className="h-16 w-3/4 self-start" />
          <SkeletonBlock className="h-10 w-1/2 self-end" />
          <SkeletonBlock className="h-24 w-4/5 self-start" />
        </div>
      </div>
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div className="flex-1 w-full overflow-y-auto">
      <div className="dashboard-page">
        <SkeletonBlock className="h-6 w-32 mb-4" />
        <div className="dashboard-header">
          <SkeletonBlock className="h-7 w-56 mb-2" />
          <SkeletonBlock className="h-4 w-full max-w-md" />
        </div>
        <div className="topic-card-grid mt-4">
          <SkeletonBlock className="h-32" />
          <SkeletonBlock className="h-32" />
          <SkeletonBlock className="h-32" />
        </div>
      </div>
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="flex flex-1 items-center justify-center p-6">
      <div className="w-full max-w-sm rounded-lg border border-rule bg-paper-raised p-6">
        <SkeletonBlock className="h-5 w-40 mb-3" />
        <SkeletonBlock className="h-4 w-full mb-2" />
        <SkeletonBlock className="h-4 w-3/4 mb-4" />
        <SkeletonBlock className="h-9 w-full" />
      </div>
    </div>
  );
}

export function DocumentSkeleton() {
  return (
    <div className="flex flex-1 flex-col gap-3 p-6">
      <SkeletonBlock className="h-6 w-1/3" />
      <SkeletonBlock className="h-4 w-full" />
      <SkeletonBlock className="h-4 w-full" />
      <SkeletonBlock className="h-4 w-5/6" />
      <SkeletonBlock className="h-64 w-full mt-2" />
    </div>
  );
}
