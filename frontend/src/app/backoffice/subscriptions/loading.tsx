import { Skeleton } from "@/components/ui/skeleton";

export default function BackofficeSubscriptionsLoading() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-44 rounded" />
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-14 rounded-lg" />)}
      </div>
    </div>
  );
}
