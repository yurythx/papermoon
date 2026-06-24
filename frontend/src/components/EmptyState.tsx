import Link from "next/link";

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: { label: string; href: string };
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-12 h-12 bg-surface-2 rounded-full border border-border-subtle flex items-center justify-center mb-4">
        <div className="w-5 h-5 border-2 border-border-default rounded-sm" />
      </div>
      <p className="text-sm font-medium text-text-primary">{title}</p>
      {description && <p className="text-xs text-text-tertiary mt-1 max-w-xs">{description}</p>}
      {action && (
        <Link
          href={action.href}
          className="mt-4 text-xs font-medium text-text-primary border border-border-default px-3 py-1.5 rounded-lg hover:bg-surface-2 transition-colors"
        >
          {action.label}
        </Link>
      )}
    </div>
  );
}
