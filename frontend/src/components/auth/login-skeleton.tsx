import { Skeleton } from "@/components/ui/skeleton";

export default function LoginLoadingSkeleton() {
  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-background px-4">
      <div className="w-full max-w-md">
        <div className="rounded-xl border border-border/50 bg-card shadow-lg p-8 space-y-6">

          {/* Logo + title */}
          <div className="flex flex-col items-center gap-3">
            <Skeleton className="h-9 w-9 rounded-lg" />
            <Skeleton className="h-7 w-32" />
            <Skeleton className="h-4 w-56" />
          </div>

          {/* OAuth buttons */}
          <div className="space-y-3">
            <Skeleton className="h-10 w-full rounded-lg" />
            <Skeleton className="h-10 w-full rounded-lg" />
          </div>

          {/* Divider */}
          <div className="flex items-center gap-3">
            <Skeleton className="h-px flex-1" />
            <Skeleton className="h-4 w-6" />
            <Skeleton className="h-px flex-1" />
          </div>

          {/* Fields */}
          <div className="space-y-4">
            <div className="space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-10 w-full rounded-md" />
            </div>
            <div className="space-y-2">
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-10 w-full rounded-md" />
            </div>
          </div>

          {/* Turnstile */}
          <Skeleton className="h-16 w-full rounded-lg" />

          {/* Submit */}
          <Skeleton className="h-11 w-full rounded-lg" />

          {/* Links */}
          <div className="flex justify-between">
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-4 w-24" />
          </div>
        </div>
      </div>
    </div>
  );
}
