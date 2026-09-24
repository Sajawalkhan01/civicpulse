import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion, type Variants } from "framer-motion";
import {
  Activity,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  Clock,
  Loader2,
  ShieldCheck,
  XCircle,
  Zap,
} from "lucide-react";

import { ComplaintForm } from "@/pages/submit-page";
import { CategoryBadge } from "@/components/badges";
import { Skeleton } from "@/components/ui/skeleton";
import { getStats, listComplaints } from "@/api/complaints";
import type { ComplaintOut, Status } from "@/api/types";
import { cn } from "@/lib/utils";

const MotionLink = motion(Link);

export default function HomePage() {
  return (
    <div className="relative overflow-hidden">
      <AmbientBackground />
      <Hero />
      <FeatureCards />
      <TrySection />
      <ActivityPreview />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Ambient background -- soft grid texture + two slow-drifting light orbs.
// ---------------------------------------------------------------------------

function AmbientBackground() {
  return (
    <>
      <div className="bg-grid-pattern pointer-events-none absolute inset-0 -z-20 opacity-80" aria-hidden="true" />
      <div
        className="pointer-events-none absolute left-1/2 top-0 -z-10 h-[1000px] w-full max-w-7xl -translate-x-1/2 overflow-hidden"
        aria-hidden="true"
      >
        <motion.div
          className="absolute -top-24 left-[10%] h-[500px] w-[500px] rounded-full bg-primary/25 blur-[110px]"
          animate={{ scale: [1, 1.08, 1] }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute top-16 right-[8%] h-[420px] w-[420px] rounded-full bg-accent/20 blur-[100px]"
          animate={{ scale: [1, 1.1, 1] }}
          transition={{ duration: 12, repeat: Infinity, ease: "easeInOut", delay: 1 }}
        />
        <motion.div
          className="absolute bottom-0 left-[30%] h-[480px] w-[480px] rounded-full bg-primary/15 blur-[130px]"
          animate={{ scale: [1, 1.06, 1] }}
          transition={{ duration: 14, repeat: Infinity, ease: "easeInOut", delay: 2 }}
        />
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Hero
// ---------------------------------------------------------------------------

const heroContainer: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.09, delayChildren: 0.05 } },
};

const heroItem: Variants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: "easeOut" } },
};

function Hero() {
  return (
    <section className="mx-auto flex max-w-4xl flex-col items-center px-4 pb-12 pt-8 text-center sm:px-6">
      <motion.div initial="hidden" animate="show" variants={heroContainer} className="flex flex-col items-center">
        <motion.div variants={heroItem}>
          <LiveStatBadge />
        </motion.div>

        <motion.div variants={heroItem} className="relative mb-6 mt-8">
          <div className="absolute -inset-1 rounded-2xl bg-primary opacity-30 blur-lg" aria-hidden="true" />
          <div className="glow-effect relative flex h-16 w-16 items-center justify-center rounded-2xl bg-primary text-primary-foreground sm:h-20 sm:w-20">
            <Activity className="h-7 w-7 sm:h-8 sm:w-8" aria-hidden="true" />
          </div>
        </motion.div>

        <motion.h1
          variants={heroItem}
          className="mb-4 font-display text-4xl font-extrabold tracking-tight text-foreground sm:text-6xl md:text-7xl"
        >
          Civic<span className="text-primary">Pulse</span>
        </motion.h1>

        <motion.p variants={heroItem} className="mb-10 max-w-2xl text-lg leading-relaxed text-muted-foreground sm:text-xl">
          Report it. Track it. Get it fixed.
        </motion.p>

        <motion.div variants={heroItem} className="flex w-full max-w-md flex-col items-center justify-center gap-4 sm:flex-row">
          <MotionLink
            to="/submit"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            transition={{ duration: 0.12, ease: "easeOut" }}
            className="inline-flex w-full items-center justify-center gap-3 rounded-2xl bg-primary px-8 py-4 text-base font-semibold text-primary-foreground shadow-lg transition-colors hover:bg-primary-hover sm:w-auto"
          >
            <span>Report an Issue</span>
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </MotionLink>

          <MotionLink
            to="/dashboard"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            transition={{ duration: 0.12, ease: "easeOut" }}
            className="glass-panel inline-flex w-full items-center justify-center gap-2 rounded-2xl px-6 py-4 text-base font-semibold text-foreground shadow-sm sm:w-auto"
          >
            <BarChart3 className="h-4 w-4 text-primary" aria-hidden="true" />
            <span>View Public Board</span>
          </MotionLink>
        </motion.div>

        <motion.div variants={heroItem} className="mt-12 flex items-center justify-center gap-6 text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <Zap className="h-3.5 w-3.5 text-accent" aria-hidden="true" /> Automated AI Triage
          </span>
          <span className="h-1 w-1 rounded-full bg-border-strong" aria-hidden="true" />
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="h-3.5 w-3.5 text-primary" aria-hidden="true" /> No Account Needed
          </span>
        </motion.div>
      </motion.div>
    </section>
  );
}

function LiveStatBadge() {
  const [total, setTotal] = useState<number | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getStats()
      .then(({ stats }) => {
        if (cancelled) return;
        // /api/stats breaks counts down by category/priority, not by status
        // or time window, so "reported so far" is the honest live number
        // available from the existing endpoint -- not a fabricated
        // "resolved this month" figure the backend doesn't compute.
        const sum = Object.values(stats.by_category).reduce((acc, n) => acc + (n ?? 0), 0);
        setTotal(sum);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (failed) return null;

  return (
    <div
      className="glass-panel animate-float inline-flex items-center gap-2.5 rounded-full px-4 py-1.5 text-xs font-medium text-primary shadow-sm sm:text-sm"
      aria-live="polite"
    >
      <span className="relative flex h-2.5 w-2.5 shrink-0">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-75" />
        <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-success" />
      </span>
      {total === null ? (
        <Skeleton className="h-4 w-40" />
      ) : (
        <span>
          <strong className="font-bold text-foreground">{total.toLocaleString()}</strong> issues reported and triaged
          by CivicPulse so far
        </span>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Feature cards / how it works
// ---------------------------------------------------------------------------

const FEATURES = [
  {
    icon: ClipboardList,
    title: "Report",
    tag: "Step 1",
    description: "Describe the issue and where it is — takes less than a minute, no account needed.",
    meta: "Get started",
    linkTo: "#demo",
  },
  {
    icon: CheckCircle2,
    title: "Dashboard",
    tag: "Goal",
    description: "Track it on the dashboard as it moves from open to in progress to resolved.",
    meta: "View dashboard",
    linkTo: "/dashboard",
  },
  {
    icon: BarChart3,
    title: "Stats",
    tag: "Live",
    description: "See aggregate counts by category and priority, updated in real time.",
    meta: "View stats",
    linkTo: "/stats",
  },
];

const cardContainer: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.15 } },
};

const cardItem: Variants = {
  hidden: { opacity: 0, y: 28 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
};

function FeatureCards() {
  return (
    <motion.section
      id="how-it-works"
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: "-100px" }}
      variants={cardContainer}
      className="relative mx-auto mt-6 max-w-5xl px-4 sm:px-6"
    >
      <div className="mb-10 text-center">
        <h2 className="mb-2 text-xs font-bold uppercase tracking-widest text-primary">How CivicPulse Works</h2>
        <p className="text-2xl font-bold text-foreground sm:text-3xl">Seamless civic resolution in three steps</p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:gap-8 md:grid-cols-3">
        {FEATURES.map((feature) => (
          <motion.div
            key={feature.title}
            variants={cardItem}
            whileHover={{ y: -4 }}
            className="glass-panel group relative flex flex-col justify-between overflow-hidden rounded-3xl p-7 shadow-sm transition-shadow duration-300 hover:shadow-xl"
          >
            <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
            <div>
              <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-2xl border border-primary/20 bg-primary/10 text-primary transition-transform duration-300 group-hover:scale-110">
                <feature.icon className="h-5 w-5" aria-hidden="true" />
              </div>
              <h3 className="mb-2 flex items-center justify-between text-xl font-bold text-foreground">
                {feature.title}
                <span className="rounded-full bg-surface-2 px-2.5 py-1 text-xs font-semibold text-muted-foreground">
                  {feature.tag}
                </span>
              </h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{feature.description}</p>
            </div>

            <CardLink to={feature.linkTo} label={feature.meta} />
          </motion.div>
        ))}
      </div>
    </motion.section>
  );
}

function CardLink({ to, label }: { to: string; label: string }) {
  const className = "mt-6 flex items-center border-t border-border pt-4 text-xs font-semibold text-primary";
  const content = (
    <>
      <span>{label}</span>
      <ChevronRight className="ml-auto h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
    </>
  );
  if (to.startsWith("#")) {
    return (
      <a href={to} className={className}>
        {content}
      </a>
    );
  }
  return (
    <Link to={to} className={className}>
      {content}
    </Link>
  );
}

// ---------------------------------------------------------------------------
// "Try it live" -- the real submit form (ComplaintForm, same one /submit
// uses), embedded directly rather than a fake simulated demo.
// ---------------------------------------------------------------------------

function TrySection() {
  return (
    <section id="demo" className="mx-auto mt-20 max-w-3xl px-4 sm:px-6">
      <div className="glass-panel relative overflow-hidden rounded-3xl p-6 shadow-xl sm:p-10">
        <div className="mb-8 flex flex-col gap-4 border-b border-border pb-6 sm:flex-row sm:items-center sm:justify-between">
          <span className="text-xs font-bold uppercase tracking-widest text-primary">Try it out live</span>
          <div className="flex w-fit items-center gap-2 rounded-full bg-surface-2 px-3 py-1.5 text-xs text-muted-foreground">
            <ShieldCheck className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
            <span>Real triage, real backend</span>
          </div>
        </div>

        <ComplaintForm />
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Recent activity preview -- real complaints from the live API (not the
// reference's hardcoded placeholder cards).
// ---------------------------------------------------------------------------

const STATUS_PILL: Record<Status, { label: string; icon: typeof Clock; className: string }> = {
  open: { label: "Open", icon: Clock, className: "bg-info-bg text-info" },
  in_progress: { label: "In progress", icon: Loader2, className: "bg-warning-bg text-warning" },
  resolved: { label: "Resolved", icon: CheckCircle2, className: "bg-success-bg text-success" },
  rejected: { label: "Rejected", icon: XCircle, className: "bg-danger-bg text-danger" },
};

function ActivityStatusPill({ status }: { status: Status }) {
  const meta = STATUS_PILL[status];
  const Icon = meta.icon;
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold", meta.className)}>
      <Icon className={cn("h-2.5 w-2.5", status === "in_progress" && "animate-spin")} aria-hidden="true" />
      {meta.label}
    </span>
  );
}

function ActivityPreview() {
  const [items, setItems] = useState<ComplaintOut[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    listComplaints({ page: 1, page_size: 3 })
      .then((result) => {
        if (!cancelled) setItems(result.items);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (failed) return null;

  return (
    <section id="dashboard-preview" className="mx-auto mt-20 max-w-5xl px-4 pb-24 sm:px-6">
      <div className="mb-8 flex flex-col items-center justify-between gap-4 sm:flex-row">
        <div className="text-center sm:text-left">
          <h2 className="text-2xl font-bold text-foreground">Recent Civic Activity</h2>
          <p className="text-sm text-muted-foreground">Real reports, straight from the live dashboard</p>
        </div>
        <Link
          to="/dashboard"
          className="flex items-center gap-1.5 rounded-full bg-surface-2 px-4 py-2 text-xs font-semibold text-foreground transition hover:bg-border"
        >
          View full dashboard
          <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
        </Link>
      </div>

      {items === null ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-28 w-full rounded-2xl" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <p className="text-center text-sm text-muted-foreground">No complaints yet — be the first to report one.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {items.map((complaint) => (
            <div key={complaint.id} className="glass-panel rounded-2xl p-4 shadow-sm">
              <div className="mb-2 flex items-center justify-between gap-2">
                <CategoryBadge category={complaint.category} className="text-[10px]" />
                <ActivityStatusPill status={complaint.status} />
              </div>
              <h3 className="truncate text-sm font-bold text-foreground">{complaint.text}</h3>
              <p className="mt-1 truncate text-xs text-muted-foreground">{complaint.location}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
