/**
 * SYNTHRA Frontend API Service Layer
 *
 * All endpoints strictly map to existing backend routes.
 * Endpoints not yet implemented are marked with AWAITING_BACKEND.
 */

const getBaseUrl = () => {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== "undefined") {
    if (window.location.port === "3000") {
      return "http://localhost:8000";
    }
    return "/api";
  }
  return "http://localhost:8000";
};

const BASE_URL = getBaseUrl();

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${path} failed (${res.status}): ${text}`);
  }
  return res.json() as Promise<T>;
}

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${path} failed (${res.status}): ${text}`);
  }
  return res.json() as Promise<T>;
}

// ─────────────────────────────────────────────
//  Types matching the backend Pydantic models
// ─────────────────────────────────────────────

export interface HealthResponse {
  status: string;
}

export interface MemoryStatus {
  backend: string;
  campaign_count: number;
  simulations_executed: number;
}

export interface CandidateQueueInfo {
  size: number;
  candidates: CandidateInfo[];
}

export interface StatusResponse {
  version: string;
  uptime_seconds: number;
  memory: MemoryStatus;
  campaign_counts: Record<string, number>;
  active_workers: number;
  queue_sizes: Record<string, number>;
  simulations: number;
  candidate_queue: CandidateQueueInfo;
  current_campaigns: string[];
  governor_state: string;
}

export interface WorkerInfo {
  worker_id: number;
  is_alive: boolean;
  name: string;
}

export interface QueueCampaignInfo {
  id: string;
  name: string;
  priority: number;
}

export interface CandidateInfo {
  candidate_id: string;
  campaign_id: string;
  hypothesis_id: string;
  expression: string;
  metrics: Record<string, unknown>;
  generation: number;
}

export interface SystemInfo {
  database_backend: string;
  campaign_count: number;
  simulations_executed: number;
  active_workers: number;
  queue_sizes: Record<string, number>;
}

export interface GovernorInfo {
  status: string;
  worker_count: number;
  max_retries: number;
  initial_backoff: number;
}

export interface CampaignInfo {
  id: string;
  name: string;
  region: string;
  universe: string;
  budget_limit: number;
  budget_spent: number;
  target_alpha_count: number;
  max_simulations: number;
  status: string;
  state: string;
}

export interface CampaignsListResponse {
  campaigns: CampaignInfo[];
  total: number;
}

export interface TelemetryEvent {
  event_type: string;
  [key: string]: unknown;
}

export interface LoginRequest {
  username: string;
  password: string;
  remember: boolean;
}

export interface LoginResponse {
  status: "success" | "verification_required" | "error";
  message?: string;
  verification_url?: string;
}

export interface LogoutResponse {
  status: "success" | "error";
  message?: string;
}

export type AuthState =
  | "Logged Out"
  | "Authenticating"
  | "Waiting for Biometric Verification"
  | "Authenticated"
  | "Session Refreshing"
  | "Session Expired";

export interface AuthStatusResponse {
  authenticated: boolean;
  username: string | null;
  state: AuthState;
  verification_url: string | null;
}

// ─────────────────────────────────────────────
//  Live API calls (backed by real endpoints)
// ─────────────────────────────────────────────

export const api = {
  health: () => fetchJSON<HealthResponse>("/health"),
  status: () => fetchJSON<StatusResponse>("/status"),
  metrics: () => fetchJSON<Record<string, unknown>>("/metrics"),
  workers: () => fetchJSON<WorkerInfo[]>("/workers"),
  queue: () => fetchJSON<QueueCampaignInfo[]>("/queue"),
  candidates: () => fetchJSON<CandidateInfo[]>("/candidates"),
  events: () => fetchJSON<TelemetryEvent[]>("/events"),
  system: () => fetchJSON<SystemInfo>("/system"),
  governor: () => fetchJSON<GovernorInfo>("/governor"),
  campaigns: () => fetchJSON<CampaignsListResponse>("/campaigns"),
  login: (data: LoginRequest) => postJSON<LoginResponse>("/auth/login", data),
  logout: () => postJSON<LogoutResponse>("/auth/logout", {}),
  authStatus: () => fetchJSON<AuthStatusResponse>("/auth/status"),
};

// ─────────────────────────────────────────────
//  AWAITING_BACKEND — endpoints not yet in the
//  backend but typed here for future wiring
// ─────────────────────────────────────────────

/** @AWAITING_BACKEND GET /campaigns/{id} */
export type CampaignDetail = CampaignInfo & {
  hypotheses: unknown[];
  simulations: unknown[];
  candidates: CandidateInfo[];
  logs: string[];
};

/** @AWAITING_BACKEND GET /research/history */
export interface ResearchHistory {
  prompt_id: string;
  prompt: string;
  reasoning: string;
  hypotheses: string[];
  timestamp: string;
}

/** @AWAITING_BACKEND GET /simulations */
export interface SimulationRecord {
  id: string;
  campaign_id: string;
  expression: string;
  status: "running" | "queued" | "completed" | "failed" | "retrying";
  sharpe: number | null;
  fitness: number | null;
  turnover: number | null;
  margin: number | null;
  started_at: string | null;
  completed_at: string | null;
}

/** @AWAITING_BACKEND GET /knowledge */
export interface KnowledgeRecord {
  datasets: string[];
  operators: string[];
  learned_rules: string[];
  failure_patterns: string[];
  successful_mutations: string[];
}

/** @AWAITING_BACKEND GET /evolution/lineage */
export interface LineageNode {
  id: string;
  parent_id: string | null;
  expression: string;
  generation: number;
  fitness: number | null;
}
