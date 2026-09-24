import type { components } from "./schema";

export type Category = components["schemas"]["Category"];
export type Priority = components["schemas"]["Priority"];
export type Status = components["schemas"]["Status"];
export type ComplaintOut = components["schemas"]["ComplaintOut"];
export type ComplaintCreate = components["schemas"]["ComplaintCreate"];
export type ComplaintListOut = components["schemas"]["ComplaintListOut"];

export const CATEGORIES: Category[] = ["water", "electricity", "sanitation", "roads", "streetlights", "other"];
export const PRIORITIES: Priority[] = ["high", "normal", "low"];
export const STATUSES: Status[] = ["open", "in_progress", "resolved", "rejected"];

// /api/stats has no response_model on the backend (routes/stats.py returns a
// plain dict), so openapi-typescript can only infer `{[key: string]: unknown}`
// from the schema. This mirrors the real shape produced by
// ComplaintRepository.stats().
export interface StatsResponse {
  by_category: Partial<Record<Category, number>>;
  by_priority: Partial<Record<Priority, number>>;
}

// Bodies produced by main.py's custom exception handlers (ComplaintNotFoundError
// -> 404, InvalidTransitionError -> 409). Neither is a FastAPI response_model,
// so neither appears in the generated OpenAPI schema/types -- this is written
// by hand to match main.py exactly.
export interface ApiErrorBody {
  error: string;
  message: string;
  [key: string]: unknown;
}
