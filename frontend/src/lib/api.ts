/**
 * Typed API client for the FastAPI backend.
 * Base URL is configured via NEXT_PUBLIC_API_URL.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

// ---------- Types ----------

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
}

export interface AttackScenario {
  id: number;
  scenario_id: string;
  name: string;
  description: string;
  target_model_type: string;
  compliance_frameworks: string[];
  attack_techniques: string[];
  vendor_promise_tested: string;
  default_prompts: string[];
}

export interface ModelOption {
  adapter: string;
  model: string;
  type: string;
  vendor: string;
}

export interface ModelRun {
  id: number;
  model_name: string;
  model_vendor: string;
  model_type: string;
  response_text: string;
  status: string;
  error_message: string | null;
  evaluation: {
    leakage_detected: boolean;
    risk_score: number;
    risk_level: string;
    leakage_categories: string[];
  } | null;
}

export interface Variant {
  id: number;
  technique: string;
  variant_text: string;
  model_runs: ModelRun[];
}

export interface BaselinePrompt {
  id: number;
  prompt_text: string;
  variants: Variant[];
}

export interface TestRunDetails {
  id: number;
  test_name: string;
  status: string;
  attack_scenario: { id: number; name: string; description: string };
  techniques: string[];
  target_models: ModelOption[];
  baseline_prompts: BaselinePrompt[];
  total_variants: number;
  total_runs: number;
  runs_completed: number;
  vulnerabilities_found: number;
  avg_risk_score: number | null;
  risk_level: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface RunTestRequest {
  test_name: string;
  description?: string;
  attack_scenario_id: number;
  baseline_prompts: string[];
  techniques: string[];
  target_models: ModelOption[];
  variants_per_technique?: number;
}

export interface RunTestResponse {
  test_id: number;
  status: string;
  message: string;
  runs_completed: number;
  vulnerabilities_found: number;
}

// ---------- Fetch helper ----------

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

// ---------- Public API ----------

export const api = {
  health: () => request<HealthResponse>("/api/v1/health"),
  listScenarios: () => request<AttackScenario[]>("/api/v1/attack-scenarios"),
  listModels: () =>
    request<{ models: ModelOption[] }>("/api/v1/models").then((r) => r.models),
  runTest: (body: RunTestRequest) =>
    request<RunTestResponse>("/api/v1/security-tests/run", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getTest: (id: number) => request<TestRunDetails>(`/api/v1/security-tests/${id}`),
};
