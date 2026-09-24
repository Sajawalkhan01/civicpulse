import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

import StatsPage from "@/pages/stats-page";
import { getStats } from "@/api/complaints";
import type { StatsResult } from "@/api/complaints";

vi.mock("@/api/complaints", async () => {
  const actual = await vi.importActual<typeof import("@/api/complaints")>("@/api/complaints");
  return { ...actual, getStats: vi.fn() };
});

const mockedGetStats = vi.mocked(getStats);

const STATS: StatsResult["stats"] = {
  by_category: { water: 4, roads: 2 },
  by_priority: { high: 1, normal: 5 },
};

beforeEach(() => {
  mockedGetStats.mockReset();
});

describe("StatsPage cache indicator", () => {
  it("shows the cached indicator when the last fetch was an X-Cache: HIT", async () => {
    mockedGetStats.mockResolvedValueOnce({ stats: STATS, cacheStatus: "HIT" });
    render(<StatsPage />);

    const indicator = await screen.findByTestId("cache-indicator");
    expect(indicator).toHaveTextContent(/cached/i);
    expect(screen.queryByText(/fetched live/i)).not.toBeInTheDocument();
  });

  it("shows the fetched-live indicator when the last fetch was an X-Cache: MISS", async () => {
    mockedGetStats.mockResolvedValueOnce({ stats: STATS, cacheStatus: "MISS" });
    render(<StatsPage />);

    const indicator = await screen.findByTestId("cache-indicator");
    expect(indicator).toHaveTextContent(/fetched live/i);
    expect(screen.queryByText(/⚡ cached/i)).not.toBeInTheDocument();
  });
});
