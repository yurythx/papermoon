import { Skeleton } from "@/components/ui/skeleton";

export default function BackofficeProductsLoading() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Skeleton className="h-8 w-36 rounded" />
        <Skeleton className="h-9 w-40 rounded" />
      </div>
      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
        {[1, 2, 3].map((i) => <Skeleton key={i} className="h-56 rounded-xl" />)}
      </div>
    </div>
  );
}
