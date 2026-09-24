import { Activity } from "lucide-react";

export function Footer() {
  return (
    <footer className="mt-auto w-full border-t border-border bg-background/80 px-4 py-8 text-center text-xs text-muted-foreground backdrop-blur">
      <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-4 sm:flex-row">
        <div className="flex items-center gap-2">
          <span className="flex h-5 w-5 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Activity className="h-3 w-3" aria-hidden="true" />
          </span>
          <span className="font-semibold text-foreground">CivicPulse</span>
          <span>— Civic Issue Tracking Platform</span>
        </div>
        <p>Clean, minimal, and community-driven.</p>
      </div>
    </footer>
  );
}
