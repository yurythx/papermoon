import { Skeleton } from "@/components/ui/skeleton";

export default function TeamLoading() {
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <Skeleton className="h-8 w-32 rounded" />
        <Skeleton className="h-9 w-36 rounded" />
      </div>
      <div className="space-y-3">
        {[1, 2, 3].map((i) => <Skeleton key={i} className="h-16 rounded-xl" />)}
      </div>
      <Skeleton className="h-6 w-28 rounded" />
      <div className="space-y-3">
        {[1, 2].map((i) => <Skeleton key={i} className="h-14 rounded-xl" />)}
      </div>
    </div>
  );
}
