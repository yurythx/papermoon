import { Skeleton } from "@/components/ui/skeleton";

export default function BackofficeLoading() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-48 rounded" />
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-24 rounded-xl" />)}
      </div>
      <Skeleton className="h-64 rounded-xl" />
    </div>
  );
}
