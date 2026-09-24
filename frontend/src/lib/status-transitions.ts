import type { Status } from "@/api/types";

// Mirrors backend/app/domain/state_machine.py -- used only to decide which
// "advance to" options the dashboard offers per row. The backend remains the
// actual authority: if this ever drifts out of sync, the PATCH still 409s
// and the UI rolls back and surfaces the server's message verbatim.
const TRANSITIONS: Record<Status, Status[]> = {
  open: ["in_progress", "rejected"],
  in_progress: ["resolved", "rejected"],
  resolved: [],
  rejected: [],
};

export function nextStatusOptions(current: Status): Status[] {
  return TRANSITIONS[current];
}
