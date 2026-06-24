import { Skeleton } from "@/components/ui/skeleton";

export default function LicenseDetailLoading() {
  return (
    <div className="space-y-8 max-w-2xl">
      <Skeleton className="h-4 w-24 rounded" />

      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <Skeleton className="h-8 w-52 rounded" />
          <Skeleton className="h-3 w-40 rounded" />
        </div>
        <Skeleton className="h-6 w-20 rounded-full" />
      </div>

      <div className="bg-surface-1 border border-border-subtle rounded-xl divide-y divide-border-subtle overflow-hidden">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex justify-between px-5 py-3.5">
            <Skeleton className="h-3 w-20 rounded" />
            <Skeleton className="h-3 w-28 rounded" />
          </div>
        ))}
      </div>

      <div className="space-y-3">
        <Skeleton className="h-4 w-36 rounded" />
        {[1, 2].map((i) => (
          <Skeleton key={i} className="h-14 w-full rounded-lg" />
        ))}
      </div>
    </div>
  );
}
