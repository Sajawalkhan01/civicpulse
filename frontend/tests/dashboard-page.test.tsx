import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { toast } from "sonner";

import DashboardPage from "@/pages/dashboard-page";
import { ApiError, listComplaints, updateComplaintStatus } from "@/api/complaints";
import type { ComplaintOut } from "@/api/types";

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
  Toaster: () => null,
}));

vi.mock("@/api/complaints", async () => {
  const actual = await vi.importActual<typeof import("@/api/complaints")>("@/api/complaints");
  return { ...actual, listComplaints: vi.fn(), updateComplaintStatus: vi.fn() };
});

const mockedList = vi.mocked(listComplaints);
const mockedUpdateStatus = vi.mocked(updateComplaintStatus);

function complaint(overrides: Partial<ComplaintOut> = {}): ComplaintOut {
  return {
    id: "22222222-2222-2222-2222-222222222222",
    text: "Pothole on Main Street outside the pharmacy",
    location: "Main Street",
    reporter_contact: null,
    category: "roads",
    priority: "normal",
    status: "open",
    ai_summary: "Pothole reported on Main Street.",
    triaged_by: "simulated",
    triage_latency_ms: 80,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

beforeEach(() => {
  mockedList.mockReset();
  mockedUpdateStatus.mockReset();
  vi.mocked(toast.success).mockReset();
  vi.mocked(toast.error).mockReset();
});

describe("DashboardPage status updates", () => {
  it("optimistically shows the new status, then rolls it back and surfaces the server's 409 message verbatim on conflict", async () => {
    const row = complaint();
    mockedList.mockResolvedValue({ items: [row], total: 1 });

    // "open" can only advance to "in_progress" or "rejected" (see
    // lib/status-transitions.ts / backend state_machine.py) -- "resolved"
    // isn't even offered as an option, so the conflict has to be simulated
    // on a transition the row actually exposes.
    const conflictMessage = "Cannot transition complaint from 'open' to 'in_progress'";
    // A promise we reject manually (rather than mockRejectedValueOnce, which
    // rejects on the very next microtask) so the optimistic "In progress"
    // state is reliably observable before the rollback happens, instead of
    // racing a `waitFor` poll against an almost-instant rejection.
    let rejectUpdate!: (reason: unknown) => void;
    mockedUpdateStatus.mockReturnValueOnce(
      new Promise((_resolve, reject) => {
        rejectUpdate = reject;
      })
    );

    const user = userEvent.setup();
    render(<DashboardPage />);

    const rowEl = await screen.findByTestId("complaint-row");
    expect(within(rowEl).getByText("Open")).toBeInTheDocument();

    await user.click(within(rowEl).getByRole("combobox", { name: /change status/i }));
    await user.click(await screen.findByRole("option", { name: /mark as in progress/i }));

    // Optimistic: the row shows "In progress" immediately, before the
    // (still-pending, mocked) request has resolved at all.
    await waitFor(() => expect(within(rowEl).getByText("In progress")).toBeInTheDocument());

    // Once the 409 comes back, it rolls back to the real status and the
    // toast carries the server's exact message -- not a generic fallback.
    rejectUpdate(new ApiError(409, { error: "invalid_transition", message: conflictMessage }, conflictMessage));
    await waitFor(() => expect(within(rowEl).getByText("Open")).toBeInTheDocument());
    expect(toast.error).toHaveBeenCalledWith(conflictMessage);
  });

  it("keeps the optimistic status and confirms with a toast when the update succeeds", async () => {
    const row = complaint();
    mockedList.mockResolvedValue({ items: [row], total: 1 });
    mockedUpdateStatus.mockResolvedValueOnce({ ...row, status: "in_progress" });

    const user = userEvent.setup();
    render(<DashboardPage />);

    const rowEl = await screen.findByTestId("complaint-row");
    await user.click(within(rowEl).getByRole("combobox", { name: /change status/i }));
    await user.click(await screen.findByRole("option", { name: /mark as in progress/i }));

    await waitFor(() => expect(within(rowEl).getByText("In progress")).toBeInTheDocument());
    expect(toast.error).not.toHaveBeenCalled();
    expect(toast.success).toHaveBeenCalled();
  });
});
