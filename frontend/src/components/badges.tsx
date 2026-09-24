import { Construction, Droplet, HelpCircle, Lightbulb, Trash2, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Category, Priority, Status } from "@/api/types";

const CATEGORY_META: Record<Category, { label: string; icon: typeof Droplet }> = {
  water: { label: "Water", icon: Droplet },
  electricity: { label: "Electricity", icon: Zap },
  sanitation: { label: "Sanitation", icon: Trash2 },
  roads: { label: "Roads", icon: Construction },
  streetlights: { label: "Streetlights", icon: Lightbulb },
  other: { label: "Other", icon: HelpCircle },
};

export function CategoryBadge({ category, className }: { category: Category; className?: string }) {
  const { label, icon: Icon } = CATEGORY_META[category];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border border-border bg-surface-2 px-2.5 py-1 text-xs font-medium text-foreground",
        className
      )}
    >
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      {label}
    </span>
  );
}

const PRIORITY_META: Record<Priority, { label: string; className: string }> = {
  high: { label: "High priority", className: "bg-danger-bg text-danger" },
  normal: { label: "Normal priority", className: "bg-info-bg text-info" },
  low: { label: "Low priority", className: "bg-surface-2 text-muted-foreground" },
};

export function PriorityBadge({ priority, className }: { priority: Priority; className?: string }) {
  const meta = PRIORITY_META[priority];
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium", meta.className, className)}>
      {meta.label}
    </span>
  );
}

const STATUS_META: Record<Status, { label: string; className: string }> = {
  open: { label: "Open", className: "bg-info-bg text-info" },
  in_progress: { label: "In progress", className: "bg-warning-bg text-warning" },
  resolved: { label: "Resolved", className: "bg-success-bg text-success" },
  rejected: { label: "Rejected", className: "bg-danger-bg text-danger" },
};

export function StatusBadge({ status, className }: { status: Status; className?: string }) {
  const meta = STATUS_META[status];
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium", meta.className, className)}>
      {meta.label}
    </span>
  );
}
