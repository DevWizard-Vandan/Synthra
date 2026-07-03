"use client";

import { AlertTriangle, RefreshCw } from "lucide-react";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-4">
      <div className="w-12 h-12 rounded-full bg-rose-500/15 flex items-center justify-center">
        <AlertTriangle className="w-6 h-6 text-rose-400" aria-hidden="true" />
      </div>
      <div className="text-center">
        <p className="text-sm font-medium text-foreground">Failed to load data</p>
        <p className="text-xs text-muted mt-1">
          {message ?? "The backend may be offline or unreachable."}
        </p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-surface-2 border border-default text-sm text-muted hover:text-foreground hover:border-[hsl(var(--border))] transition-colors"
          aria-label="Retry loading data"
        >
          <RefreshCw className="w-3.5 h-3.5" aria-hidden="true" />
          Retry
        </button>
      )}
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
}

export function EmptyState({ title, description, icon }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-4">
      {icon && (
        <div className="w-12 h-12 rounded-full bg-surface-2 flex items-center justify-center text-muted">
          {icon}
        </div>
      )}
      <div className="text-center">
        <p className="text-sm font-medium text-foreground">{title}</p>
        <p className="text-xs text-muted mt-1">{description}</p>
      </div>
    </div>
  );
}
