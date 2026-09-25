import { client } from "./client";
import type {
  ApiErrorBody,
  Category,
  ComplaintCreate,
  ComplaintListOut,
  ComplaintOut,
  Priority,
  StatsResponse,
  Status,
} from "./types";

/** Thrown for every non-2xx response. `message` is the server's own message
 * whenever one is available (validation error, 404, 409 conflict), so
 * callers can surface it verbatim instead of a generic fallback. */
export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

function extractMessage(body: unknown): string | undefined {
  if (!body || typeof body !== "object") return undefined;
  const record = body as Record<string, unknown>;
  if (typeof record.message === "string") return record.message;
  if (Array.isArray(record.detail)) {
    const messages = record.detail
      .map((entry) => (entry && typeof entry === "object" ? (entry as { msg?: unknown }).msg : undefined))
      .filter((msg): msg is string => typeof msg === "string");
    if (messages.length > 0) return messages.join("; ");
  }
  return undefined;
}

export async function createComplaint(payload: ComplaintCreate): Promise<ComplaintOut> {
  const { data, error, response } = await client.POST("/api/complaints", { body: payload });
  if (error || !data) {
    throw new ApiError(response.status, error, extractMessage(error) ?? "Couldn't submit your complaint. Please try again.");
  }
  return data;
}

export interface ListComplaintsParams {
  category?: Category;
  priority?: Priority;
  status?: Status;
  page?: number;
  page_size?: number;
}

export async function listComplaints(params: ListComplaintsParams): Promise<ComplaintListOut> {
  const { data, error, response } = await client.GET("/api/complaints", { params: { query: params } });
  if (error || !data) {
    throw new ApiError(response.status, error, extractMessage(error) ?? "Couldn't load complaints.");
  }
  return data;
}

export async function updateComplaintStatus(complaintId: string, status: Status): Promise<ComplaintOut> {
  const { data, error, response } = await client.PATCH("/api/complaints/{complaint_id}/status", {
    params: { path: { complaint_id: complaintId } },
    body: { status },
  });
  if (error || !data) {
    const body = error as ApiErrorBody | undefined;
    throw new ApiError(response.status, error, body?.message ?? extractMessage(error) ?? "Couldn't update the status.");
  }
  return data;
}

export interface StatsResult {
  stats: StatsResponse;
  cacheStatus: "HIT" | "MISS" | "UNKNOWN";
}

export async function getStats(): Promise<StatsResult> {
  const { data, error, response } = await client.GET("/api/stats", {});
  // /api/stats has no documented error response (routes/stats.py has no
  // response_model), so openapi-fetch's generated type narrows `response` to
  // `never` inside `if (error)` -- read the status out beforehand instead.
  const status = response.status;
  if (error || !data) {
    throw new ApiError(status, error, extractMessage(error) ?? "Couldn't load stats.");
  }
  const header = response.headers.get("X-Cache");
  const cacheStatus = header === "HIT" || header === "MISS" ? header : "UNKNOWN";
  return { stats: data as unknown as StatsResponse, cacheStatus };
}
