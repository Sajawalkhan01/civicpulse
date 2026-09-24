import { useCallback, useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion, type Variants } from "framer-motion";
import { ChevronLeft, ChevronRight, Inbox } from "lucide-react";
import { toast } from "sonner";

import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { CategoryBadge, PriorityBadge, StatusBadge } from "@/components/badges";
import { ApiError, listComplaints, updateComplaintStatus } from "@/api/complaints";
import { CATEGORIES, PRIORITIES, STATUSES, type Category, type ComplaintOut, type Priority, type Status } from "@/api/types";
import { nextStatusOptions } from "@/lib/status-transitions";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 10;

const CATEGORY_OPTIONS = [{ value: "all", label: "All categories" }, ...CATEGORIES.map((c) => ({ value: c, label: capitalize(c) }))];
const PRIORITY_OPTIONS = [{ value: "all", label: "All priorities" }, ...PRIORITIES.map((p) => ({ value: p, label: capitalize(p) }))];
const STATUS_OPTIONS = [{ value: "all", label: "All statuses" }, ...STATUSES.map((s) => ({ value: s, label: statusLabel(s) }))];

function capitalize(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function statusLabel(s: Status) {
  return { open: "Open", in_progress: "In progress", resolved: "Resolved", rejected: "Rejected" }[s];
}

const listVariants: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06, delayChildren: 0.04 } },
};

const rowVariants: Variants = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.25, ease: "easeOut" } },
  exit: { opacity: 0, y: -10, transition: { duration: 0.18, ease: "easeIn" } },
};

export default function DashboardPage() {
  const [category, setCategory] = useState<Category | "all">("all");
  const [priority, setPriority] = useState<Priority | "all">("all");
  const [status, setStatus] = useState<Status | "all">("all");
  const [page, setPage] = useState(1);

  const [items, setItems] = useState<ComplaintOut[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const result = await listComplaints({
        category: category === "all" ? undefined : category,
        priority: priority === "all" ? undefined : priority,
        status: status === "all" ? undefined : status,
        page,
        page_size: PAGE_SIZE,
      });
      setItems(result.items);
      setTotal(result.total);
    } catch (err) {
      setLoadError(err instanceof ApiError ? err.message : "Couldn't load complaints.");
    } finally {
      setLoading(false);
    }
  }, [category, priority, status, page]);

  useEffect(() => {
    load();
  }, [load]);

  function handleCategoryChange(value: string) {
    setCategory(value as Category | "all");
    setPage(1);
  }

  function handlePriorityChange(value: string) {
    setPriority(value as Priority | "all");
    setPage(1);
  }

  function handleStatusFilterChange(value: string) {
    setStatus(value as Status | "all");
    setPage(1);
  }

  async function handleStatusChange(complaint: ComplaintOut, next: Status) {
    const previous = complaint.status;
    setItems((current) => current.map((c) => (c.id === complaint.id ? { ...c, status: next } : c)));

    try {
      const updated = await updateComplaintStatus(complaint.id, next);
      setItems((current) => current.map((c) => (c.id === complaint.id ? updated : c)));
      toast.success(`Marked "${truncate(complaint.text, 40)}" as ${statusLabel(next).toLowerCase()}`);
    } catch (err) {
      setItems((current) => current.map((c) => (c.id === complaint.id ? { ...c, status: previous } : c)));
      if (err instanceof ApiError) {
        toast.error(err.message);
      } else {
        toast.error("Couldn't update the status. Please try again.");
      }
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const filterKey = `${category}-${priority}-${status}-${page}`;

  // category/priority/status are all sent as query params, so `items` is
  // already server-filtered at fetch time. But an optimistic status update
  // (handleStatusChange) can move one item's status away from the active
  // status filter without a re-fetch -- re-filtering client-side by status
  // here is what lets that item animate out of view instead of just
  // sitting there showing a status that contradicts the active filter.
  const visibleItems = useMemo(
    () => items.filter((c) => status === "all" || c.status === status),
    [items, status]
  );

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <header className="mb-6">
        <h1 className="font-display text-3xl font-semibold text-foreground">Dashboard</h1>
        <p className="mt-2 text-muted-foreground">Review incoming reports and move them through triage.</p>
      </header>

      <div className="mb-6 flex flex-wrap gap-3">
        <Select aria-label="Filter by category" value={category} onValueChange={handleCategoryChange} options={CATEGORY_OPTIONS} />
        <Select aria-label="Filter by priority" value={priority} onValueChange={handlePriorityChange} options={PRIORITY_OPTIONS} />
        <Select aria-label="Filter by status" value={status} onValueChange={handleStatusFilterChange} options={STATUS_OPTIONS} />
      </div>

      {loadError && (
        <div role="alert" className="mb-4 rounded-lg border border-danger/30 bg-danger-bg px-4 py-3 text-sm text-danger">
          {loadError}
        </div>
      )}

      {loading ? (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      ) : visibleItems.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-16 text-center text-muted-foreground">
          <Inbox className="h-8 w-8" aria-hidden="true" />
          <p>No complaints match these filters.</p>
        </div>
      ) : (
        <AnimatePresence mode="wait">
          {/* Keyed by filterKey: a genuine data reload (page/filter change)
              replaces this whole block, fading the old set out as one unit
              and staggering the new set in via listVariants. A status change
              on a single row (handleStatusChange) never touches filterKey, so
              this block stays mounted and only the inner AnimatePresence
              below handles that item animating out individually. */}
          <motion.div key={filterKey} variants={listVariants} initial="hidden" animate="show" className="flex flex-col gap-3">
            <AnimatePresence initial={false}>
              {visibleItems.map((complaint) => (
                <ComplaintRow key={complaint.id} complaint={complaint} onStatusChange={handleStatusChange} />
              ))}
            </AnimatePresence>
          </motion.div>
        </AnimatePresence>
      )}

      <div className="mt-6 flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {total === 0 ? "0 results" : `Page ${page} of ${totalPages} · ${total} total`}
        </p>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            <ChevronLeft className="h-4 w-4" /> Prev
          </Button>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            Next <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

function truncate(text: string, max: number) {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}

function ComplaintRow({
  complaint,
  onStatusChange,
}: {
  complaint: ComplaintOut;
  onStatusChange: (complaint: ComplaintOut, next: Status) => void;
}) {
  const options = nextStatusOptions(complaint.status);

  return (
    <motion.div
      layout
      variants={rowVariants}
      exit="exit"
      className="rounded-xl border border-border bg-surface p-4 shadow-sm sm:p-5"
      data-testid="complaint-row"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-foreground">{complaint.text}</p>
          <p className="mt-1 text-xs text-muted-foreground">{complaint.location}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <CategoryBadge category={complaint.category} />
            <PriorityBadge priority={complaint.priority} />
            <StatusBadge status={complaint.status} />
          </div>
        </div>

        <div className={cn("flex shrink-0 items-center gap-2", options.length === 0 && "opacity-50")}>
          {options.length > 0 ? (
            <Select
              aria-label={`Change status for complaint`}
              value=""
              onValueChange={(v) => onStatusChange(complaint, v as Status)}
              placeholder="Advance status…"
              options={options.map((s) => ({ value: s, label: `Mark as ${statusLabel(s).toLowerCase()}` }))}
              className="min-w-[10rem]"
            />
          ) : (
            <span className="text-xs text-muted-foreground">Final status</span>
          )}
        </div>
      </div>
    </motion.div>
  );
}
