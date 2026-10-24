// Single entry point for backend communication. Components import `api` only.
// Switch modes with VITE_API_MODE=http (real FastAPI) or mock (default).
import { httpApi } from "./http";
import { mockApi } from "./mock";
import type { ApiClient } from "./types";

export const API_MODE: "mock" | "http" = import.meta.env.VITE_API_MODE === "http" ? "http" : "mock";

export const api: ApiClient = API_MODE === "http" ? httpApi : mockApi;

export * from "./types";
