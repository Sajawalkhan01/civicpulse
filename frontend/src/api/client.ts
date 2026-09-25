import createClient from "openapi-fetch";
import type { paths } from "./schema";

// Relative base path -- never an absolute backend URL. In dev, Vite proxies
// /api/* to the backend (vite.config.ts); in prod, nginx does the same in
// front of the built static files. The backend's actual address never
// appears in frontend code or the build output.
export const client = createClient<paths>({ baseUrl: "/" });
