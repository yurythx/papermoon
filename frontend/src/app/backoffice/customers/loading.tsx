import { Skeleton } from "@/components/ui/skeleton";

export default function BackofficeCustomersLoading() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Skeleton className="h-8 w-40 rounded" />
        <Skeleton className="h-9 w-44 rounded" />
      </div>
      <Skeleton className="h-10 rounded-lg" />
      <div className="space-y-3">
        {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-14 rounded-lg" />)}
      </div>
    </div>
  );
}
