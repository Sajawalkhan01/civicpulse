import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import SubmitPage from "@/pages/submit-page";
import { createComplaint } from "@/api/complaints";
import type { ComplaintOut } from "@/api/types";

vi.mock("@/api/complaints", async () => {
  const actual = await vi.importActual<typeof import("@/api/complaints")>("@/api/complaints");
  return { ...actual, createComplaint: vi.fn() };
});

const mockedCreateComplaint = vi.mocked(createComplaint);

function baseComplaint(overrides: Partial<ComplaintOut> = {}): ComplaintOut {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    text: "There is a burst water pipe flooding the sidewalk outside the bakery.",
    location: "400 Elm Street",
    reporter_contact: null,
    category: "water",
    priority: "high",
    status: "open",
    ai_summary: "Burst water pipe flooding the sidewalk near a bakery.",
    triaged_by: "simulated",
    triage_latency_ms: 120,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

beforeEach(() => {
  mockedCreateComplaint.mockReset();
});

describe("SubmitPage validation", () => {
  it("shows inline errors for text/location that are too short and never calls the API", async () => {
    const user = userEvent.setup();
    render(<SubmitPage />);

    await user.type(screen.getByLabelText(/what's the issue/i), "too short");
    await user.type(screen.getByLabelText(/location/i), "ab");
    await user.click(screen.getByRole("button", { name: /submit complaint/i }));

    expect(await screen.findByText(/at least 10 characters/i)).toBeInTheDocument();
    expect(screen.getByText(/at least 3 characters/i)).toBeInTheDocument();
    expect(mockedCreateComplaint).not.toHaveBeenCalled();
  });
});

describe("SubmitPage success", () => {
  it("shows the server's category, priority, summary, and provider after a successful submission", async () => {
    mockedCreateComplaint.mockResolvedValueOnce(baseComplaint());
    const user = userEvent.setup();
    render(<SubmitPage />);

    await user.type(
      screen.getByLabelText(/what's the issue/i),
      "There is a burst water pipe flooding the sidewalk outside the bakery."
    );
    await user.type(screen.getByLabelText(/location/i), "400 Elm Street");
    await user.click(screen.getByRole("button", { name: /submit complaint/i }));

    expect(await screen.findByText(/thanks — we've got it/i)).toBeInTheDocument();
    expect(screen.getByText("Water")).toBeInTheDocument();
    expect(screen.getByText("High priority")).toBeInTheDocument();
    expect(screen.getByText(/burst water pipe flooding the sidewalk near a bakery/i)).toBeInTheDocument();
    expect(screen.getByText(/simulated ai/i)).toBeInTheDocument();
  });

  it("presents a rules:fallback result as a normal, non-alarming outcome rather than an error", async () => {
    mockedCreateComplaint.mockResolvedValueOnce(baseComplaint({ triaged_by: "rules:fallback" }));
    const user = userEvent.setup();
    render(<SubmitPage />);

    await user.type(
      screen.getByLabelText(/what's the issue/i),
      "There is a burst water pipe flooding the sidewalk outside the bakery."
    );
    await user.type(screen.getByLabelText(/location/i), "400 Elm Street");
    await user.click(screen.getByRole("button", { name: /submit complaint/i }));

    await waitFor(() => expect(screen.getByText(/backup rules/i)).toBeInTheDocument());
    // Still framed as a normal outcome: the complaint was still triaged and
    // accepted, so nothing on the result screen should read as an error --
    // the note uses the accent styling, not the danger/error styling.
    expect(screen.getByText(/thanks — we've got it/i)).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByText(/wasn't available for this one/i)).toBeInTheDocument();
    const note = screen.getByTestId("provider-note");
    expect(note.className).toMatch(/accent/);
    expect(note.className).not.toMatch(/danger/);
  });
});
