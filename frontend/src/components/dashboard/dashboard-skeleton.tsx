import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardPageSkeleton() {
  return (
    <div className="flex flex-col gap-6 p-6 animate-in fade-in duration-300">
      {/* Page header */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-72" />
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-xl border border-border/50 bg-card p-5 space-y-3">
            <div className="flex items-center justify-between">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-5 w-5 rounded" />
            </div>
            <Skeleton className="h-8 w-20" />
            <Skeleton className="h-3 w-32" />
          </div>
        ))}
      </div>

      {/* Main content area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Large card */}
        <div className="lg:col-span-2 rounded-xl border border-border/50 bg-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <Skeleton className="h-5 w-36" />
            <Skeleton className="h-8 w-24 rounded-md" />
          </div>
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton className="h-9 w-9 rounded-full shrink-0" />
                <div className="flex-1 space-y-1.5">
                  <Skeleton className="h-3.5 w-full max-w-xs" />
                  <Skeleton className="h-3 w-24" />
                </div>
                <Skeleton className="h-6 w-16 rounded-full" />
              </div>
            ))}
          </div>
        </div>

        {/* Sidebar card */}
        <div className="rounded-xl border border-border/50 bg-card p-5 space-y-4">
          <Skeleton className="h-5 w-28" />
          <div className="space-y-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="flex items-center justify-between">
                <Skeleton className="h-3.5 w-28" />
                <Skeleton className="h-3.5 w-12" />
              </div>
            ))}
          </div>
          <Skeleton className="h-32 w-full rounded-lg" />
        </div>
      </div>

      {/* Table skeleton */}
      <div className="rounded-xl border border-border/50 bg-card overflow-hidden">
        {/* Table header */}
        <div className="flex items-center gap-4 px-5 py-3 border-b border-border/50 bg-muted/20">
          {[40, 20, 15, 15, 10].map((w, i) => (
            <Skeleton key={i} className={`h-4 w-${w === 40 ? "40" : w === 20 ? "20" : w === 15 ? "16" : "12"}`} />
          ))}
        </div>
        {/* Table rows */}
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center gap-4 px-5 py-4 border-b border-border/30 last:border-0">
            <div className="flex items-center gap-3 flex-1">
              <Skeleton className="h-8 w-8 rounded-md shrink-0" />
              <div className="space-y-1">
                <Skeleton className="h-3.5 w-36" />
                <Skeleton className="h-3 w-24" />
              </div>
            </div>
            <Skeleton className="h-3.5 w-20" />
            <Skeleton className="h-6 w-16 rounded-full" />
            <Skeleton className="h-3.5 w-24" />
            <Skeleton className="h-8 w-8 rounded-md" />
          </div>
        ))}
      </div>
    </div>
  );
}
