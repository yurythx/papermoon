import { Skeleton } from "@/components/ui/skeleton";

export default function CatalogLoading() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-40 rounded" />
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {[1, 2, 3].map((i) => <Skeleton key={i} className="h-72 rounded-xl" />)}
      </div>
    </div>
  );
}
