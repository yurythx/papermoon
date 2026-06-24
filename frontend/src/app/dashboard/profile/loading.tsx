import { Skeleton } from "@/components/ui/skeleton";

export default function ProfileLoading() {
  return (
    <div className="space-y-8 max-w-2xl">
      <Skeleton className="h-8 w-40 rounded" />
      <div className="space-y-4">
        <Skeleton className="h-5 w-32 rounded" />
        <Skeleton className="h-10 rounded-lg" />
        <Skeleton className="h-5 w-24 rounded" />
        <Skeleton className="h-10 rounded-lg" />
        <Skeleton className="h-9 w-28 rounded-lg" />
      </div>
      <Skeleton className="h-px w-full" />
      <div className="space-y-4">
        <Skeleton className="h-6 w-36 rounded" />
        <Skeleton className="h-10 rounded-lg" />
        <Skeleton className="h-10 rounded-lg" />
        <Skeleton className="h-10 rounded-lg" />
        <Skeleton className="h-9 w-36 rounded-lg" />
      </div>
    </div>
  );
}
