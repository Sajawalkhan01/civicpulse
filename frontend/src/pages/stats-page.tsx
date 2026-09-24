import { useCallback, useEffect, useState, type ReactNode } from "react";
import { motion } from "framer-motion";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Zap, RefreshCw, CloudDownload } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { ApiError, getStats, type StatsResult } from "@/api/complaints";
import { cn } from "@/lib/utils";

function toChartData(record: Partial<Record<string, number>>, labels: Record<string, string>) {
  return Object.entries(labels).map(([key, label]) => ({ key, label, count: record[key] ?? 0 }));
}

const CATEGORY_LABELS: Record<string, string> = {
  water: "Water",
  electricity: "Electricity",
  sanitation: "Sanitation",
  roads: "Roads",
  streetlights: "Streetlights",
  other: "Other",
};

const PRIORITY_LABELS: Record<string, string> = { high: "High", normal: "Normal", low: "Low" };

export default function StatsPage() {
  const [result, setResult] = useState<StatsResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getStats();
      setResult(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load stats.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-semibold text-foreground">Stats</h1>
          <p className="mt-2 text-muted-foreground">A live snapshot of everything reported so far.</p>
        </div>
        <div className="flex items-center gap-3">
          {result && <CacheIndicator status={result.cacheStatus} />}
          <Button variant="outline" size="sm" onClick={load} disabled={loading}>
            <RefreshCw className={cn("h-3.5 w-3.5", loading && "animate-spin")} />
            Refresh
          </Button>
        </div>
      </header>

      {error && (
        <div role="alert" className="mb-6 rounded-lg border border-danger/30 bg-danger-bg px-4 py-3 text-sm text-danger">
          {error}
        </div>
      )}

      {loading && !result ? (
        <div className="grid gap-6 sm:grid-cols-2">
          <Skeleton className="h-72 w-full" />
          <Skeleton className="h-72 w-full" />
        </div>
      ) : result ? (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          className="grid gap-6 sm:grid-cols-2"
        >
          <ChartCard title="By category">
            <StatsBarChart data={toChartData(result.stats.by_category, CATEGORY_LABELS)} color="var(--color-primary)" animationBegin={0} />
          </ChartCard>
          <ChartCard title="By priority">
            <StatsBarChart
              data={toChartData(result.stats.by_priority, PRIORITY_LABELS)}
              color="var(--color-accent)"
              animationBegin={150}
            />
          </ChartCard>
        </motion.div>
      ) : null}
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
      <h2 className="mb-4 text-sm font-semibold text-foreground">{title}</h2>
      <div className="h-56">{children}</div>
    </div>
  );
}

function StatsBarChart({
  data,
  color,
  animationBegin = 0,
}: {
  data: { label: string; count: number }[];
  color: string;
  animationBegin?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
        <XAxis dataKey="label" tick={{ fill: "var(--color-muted-foreground)", fontSize: 12 }} axisLine={{ stroke: "var(--color-border)" }} tickLine={false} />
        <YAxis allowDecimals={false} tick={{ fill: "var(--color-muted-foreground)", fontSize: 12 }} axisLine={false} tickLine={false} />
        <Tooltip
          cursor={{ fill: "var(--color-surface-2)" }}
          contentStyle={{
            background: "var(--color-surface)",
            border: "1px solid var(--color-border)",
            borderRadius: 8,
            fontSize: 12,
            color: "var(--color-foreground)",
          }}
        />
        <Bar
          dataKey="count"
          fill={color}
          radius={[6, 6, 0, 0]}
          isAnimationActive
          animationBegin={animationBegin}
          animationDuration={700}
          animationEasing="ease-out"
        />
      </BarChart>
    </ResponsiveContainer>
  );
}

function CacheIndicator({ status }: { status: StatsResult["cacheStatus"] }) {
  if (status === "UNKNOWN") return null;
  const isHit = status === "HIT";
  return (
    <span
      data-testid="cache-indicator"
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium",
        isHit ? "bg-accent/15 text-accent-foreground" : "bg-info-bg text-info"
      )}
    >
      {isHit ? <Zap className="h-3.5 w-3.5" aria-hidden="true" /> : <CloudDownload className="h-3.5 w-3.5" aria-hidden="true" />}
      {isHit ? "⚡ cached" : "fetched live"}
    </span>
  );
}
