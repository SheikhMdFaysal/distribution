/**
 * Typed API client for the FastAPI backend.
 * Base URL is configured via NEXT_PUBLIC_API_URL in .env.local
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
  category: string;
}

export interface TestRun {
  id: string;
  scenario_id: string;
  model: string;
  status: "queued" | "running" | "completed" | "failed";
  cvss_score?: number;
  created_at: string;
}

/** Thin fetch wrapper with JSON parsing + error handling. */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${await res.text()}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<HealthResponse>("/api/v1/health"),
  listScenarios: () => request<Scenario[]>("/api/v1/scenarios"),
  listRuns: () => request<TestRun[]>("/api/v1/runs"),
};
