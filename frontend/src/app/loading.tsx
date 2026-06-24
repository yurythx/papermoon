import { Spinner } from "@/components/ui/spinner";

export default function RootLoading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-0">
      <Spinner size="lg" />
    </div>
  );
}
