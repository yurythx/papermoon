import { Skeleton } from "@/components/ui/skeleton";

export default function CustomerDetailLoading() {
  return (
    <div className="space-y-8 max-w-3xl">
      <Skeleton className="h-4 w-24" />
      <div className="flex items-start gap-3">
        <Skeleton className="h-10 w-10 rounded-xl" />
        <div className="space-y-2">
          <Skeleton className="h-7 w-52" />
          <Skeleton className="h-4 w-36" />
        </div>
      </div>
      <div className="flex gap-3">
        <Skeleton className="h-8 w-24 rounded-lg" />
        <Skeleton className="h-8 w-28 rounded-lg" />
      </div>
      <div className="bg-surface-1 border border-border-subtle rounded-xl divide-y divide-border-subtle">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex justify-between px-5 py-3.5">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-3 w-48" />
          </div>
        ))}
      </div>
      <div className="space-y-3">
        <Skeleton className="h-4 w-32" />
        <div className="bg-surface-1 border border-border-subtle rounded-xl divide-y divide-border-subtle">
          {[1, 2].map((i) => (
            <div key={i} className="flex justify-between px-5 py-4">
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-5 w-20 rounded-full" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
