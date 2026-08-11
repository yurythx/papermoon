import { Skeleton } from "@/components/ui/skeleton";

export default function KeycloakIntegrationLoading() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-48 rounded" />
      <Skeleton className="h-40 rounded-xl" />
    </div>
  );
}
