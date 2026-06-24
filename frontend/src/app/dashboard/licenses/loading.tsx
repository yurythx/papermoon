import { Skeleton } from "@/components/ui/skeleton";

export default function LicensesLoading() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-40 rounded" />
      <div className="space-y-4">
        {[1, 2, 3].map((i) => <Skeleton key={i} className="h-28 rounded-xl" />)}
      </div>
    </div>
  );
}
