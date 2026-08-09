/**
 * API client.
 *
 * Types here are transcribed from the FastAPI response models, not assumed.
 * Note that stored items (`StoredItem`) and freshly-analysed items
 * (`AnalyzedItem`) are NOT the same shape: the stored serialiser drops the
 * per-item `error` and adds `run_id`.
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export const API_KEY_STORAGE = "sentilytics.api_key";

/** Backend bounds, enforced client-side so a user never discovers them via a 422. */
export const MAX_ITEMS = 200;
export const MAX_CHARS = 5000;

export type UserType = "free" | "paid" | "enterprise";
export type Source =
  | "support"
  | "nps"
  | "review"
  | "app_store"
  | "slack"
  | "sales_call"
  | "other";
export type Sentiment = "positive" | "neutral" | "negative";
export type Intent =
  | "complaint"
  | "praise"
  | "feature-request"
  | "bug-report"
  | "question"
  | "other";
export type TrendDirection =
  | "emerging"
  | "spiking"
  | "steady"
  | "declining"
  | "insufficient_history";

export const USER_TYPES: UserType[] = ["free", "paid", "enterprise"];
export const SOURCES: Source[] = [
  "support",
  "nps",
  "review",
  "app_store",
  "slack",
  "sales_call",
  "other",
];

export interface Workspace {
  id: string;
  name: string;
}

export interface AuthResponse {
  api_key: string;
  email: string;
  workspace: Workspace;
}

export interface MeResponse {
  /** Null for workspaces created by the CLI, which have a key but no user. */
  email: string | null;
  workspace: Workspace;
}

export interface FeedbackInput {
  id?: string;
  text: string;
  user_type: UserType;
  source: Source;
}

export interface AnalyzedItem {
  id: string;
  text: string;
  user_type: UserType;
  source: Source;
  sentiment: Sentiment;
  emotion: string;
  intent: Intent;
  severity: number;
  feature_area: string;
  churn_risk: boolean;
  theme_id: string | null;
  status: "ok" | "failed";
  error: string | null;
}

export interface StoredItem {
  id: string;
  run_id: string;
  text: string;
  user_type: UserType;
  source: Source;
  sentiment: Sentiment | null;
  emotion: string | null;
  intent: Intent | null;
  severity: number | null;
  feature_area: string | null;
  churn_risk: boolean;
  theme_id: string | null;
  status: string;
}

export interface RejectedItem {
  id: string;
  text: string;
  reason: string;
}

export interface Theme {
  id: string;
  name: string;
  description: string;
  count: number;
  is_new: boolean;
  impact_score: number;
  avg_severity: number;
  sentiment_breakdown: Record<string, number>;
  churn_risk_count: number;
  sample_item_ids?: string[];
  share?: number;
}

export interface Trend {
  theme_id: string;
  theme_name: string;
  direction: TrendDirection;
  current_share: number;
  baseline_share: number | null;
  change_ratio: number | null;
  detail: string;
}

export interface Recommendation {
  title: string;
  rationale: string;
  theme_ids: string[];
  effort: "low" | "medium" | "high";
}

export interface AnalyzeResponse {
  run_id: string;
  summary: string;
  analyzed: AnalyzedItem[];
  rejected: RejectedItem[];
  themes: Theme[];
  trends: Trend[];
  recommendations: Recommendation[];
  revision_count: number;
}

export interface RunSummary {
  id: string;
  created_at: string;
  status: string;
  item_count: number;
  rejected_count: number;
  theme_count: number;
  summary: string | null;
  error: string | null;
}

export interface RunResult extends RunSummary {
  themes: Theme[];
  trends: Trend[];
  recommendations: Recommendation[];
  analyzed: StoredItem[];
}

export interface ThemeListItem {
  id: string;
  name: string;
  description: string;
  total_mentions: number;
  run_count: number;
  first_seen_run: string;
  created_at: string;
  updated_at: string;
}

export interface ThemeHistoryPoint {
  run_id: string;
  at: string;
  count: number;
  share: number;
  avg_severity: number;
}

export interface ThemeTrendSeries {
  id: string;
  name: string;
  total_mentions: number;
  run_count: number;
  history: ThemeHistoryPoint[];
}

export interface ThemeItemsResponse {
  theme: {
    id: string;
    name: string;
    description: string;
    total_mentions: number;
    run_count: number;
  };
  total: number;
  limit: number;
  offset: number;
  items: StoredItem[];
}

export interface ScatterPoint {
  item_id: string;
  theme_id: string | null;
  theme_name: string | null;
  x: number;
  y: number;
  z: number;
  sentiment: Sentiment | null;
  severity: number | null;
  text: string;
}

export interface ScatterResponse {
  points: ScatterPoint[];
  themes: { id: string; name: string; count: number }[];
}

/* -------------------------------------------------------------------------
   Client
------------------------------------------------------------------------- */

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

let unauthorizedHandler: (() => void) | null = null;

/** Registered by AuthProvider so any 401 drops the stored key and returns to login. */
export function onUnauthorized(handler: (() => void) | null) {
  unauthorizedHandler = handler;
}

export function readStoredKey(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(API_KEY_STORAGE);
}

export function writeStoredKey(key: string | null) {
  if (typeof window === "undefined") return;
  if (key) window.localStorage.setItem(API_KEY_STORAGE, key);
  else window.localStorage.removeItem(API_KEY_STORAGE);
}

async function extractError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    const detail = body?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) {
      // FastAPI validation errors arrive as a list of field problems.
      return detail
        .map((d: { loc?: string[]; msg: string }) =>
          d.loc?.length ? `${d.loc[d.loc.length - 1]}: ${d.msg}` : d.msg,
        )
        .join(", ");
    }
  } catch {
    /* fall through to the status text */
  }
  return response.statusText || `Request failed (${response.status})`;
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  /** Signup and login are the only calls that must not send a key. */
  anonymous?: boolean;
}

export async function request<T>(
  path: string,
  { body, anonymous, headers, ...init }: RequestOptions = {},
): Promise<T> {
  const finalHeaders = new Headers(headers);
  const key = readStoredKey();

  if (!anonymous && key) finalHeaders.set("X-API-Key", key);

  let payload: BodyInit | undefined;
  if (body instanceof FormData) {
    payload = body;
  } else if (body !== undefined) {
    finalHeaders.set("Content-Type", "application/json");
    payload = JSON.stringify(body);
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: finalHeaders,
      body: payload,
    });
  } catch {
    throw new ApiError(
      0,
      `Cannot reach the API at ${API_BASE}. Check that the backend is running.`,
    );
  }

  if (response.status === 401 && !anonymous) {
    unauthorizedHandler?.();
    throw new ApiError(401, "Your session expired. Sign in again.");
  }

  if (!response.ok) throw new ApiError(response.status, await extractError(response));

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  signup: (email: string, password: string, workspace_name?: string) =>
    request<AuthResponse>("/auth/signup", {
      method: "POST",
      anonymous: true,
      body: { email, password, workspace_name: workspace_name || undefined },
    }),

  login: (email: string, password: string) =>
    request<AuthResponse>("/auth/login", {
      method: "POST",
      anonymous: true,
      body: { email, password },
    }),

  me: () => request<MeResponse>("/auth/me"),

  analyze: (raw_feedback: FeedbackInput[]) =>
    request<AnalyzeResponse>("/analyze", { method: "POST", body: { raw_feedback } }),

  analyzeCsv: (form: FormData) =>
    request<AnalyzeResponse>("/analyze/csv", { method: "POST", body: form }),

  themes: (limit = 100) => request<ThemeListItem[]>(`/themes?limit=${limit}`),

  themeTrends: (limit = 20, history = 10) =>
    request<ThemeTrendSeries[]>(`/themes/trends?limit=${limit}&history=${history}`),

  themeItems: (id: string, limit = 50, offset = 0) =>
    request<ThemeItemsResponse>(
      `/themes/${encodeURIComponent(id)}/items?limit=${limit}&offset=${offset}`,
    ),

  runs: (limit = 50) => request<RunSummary[]>(`/runs?limit=${limit}`),

  run: (id: string) => request<RunSummary>(`/runs/${encodeURIComponent(id)}`),

  runResult: (id: string) =>
    request<RunResult>(`/runs/${encodeURIComponent(id)}/result`),

  runScatter: (id: string) =>
    request<ScatterResponse>(`/runs/${encodeURIComponent(id)}/scatter`),

  health: () => request<{ status: string }>("/health", { anonymous: true }),
};

/* -------------------------------------------------------------------------
   Streaming analysis

   EventSource cannot POST and the batch has to go in the body, so this reads
   the SSE frames off a fetch ReadableStream by hand.
------------------------------------------------------------------------- */

export type StreamEvent =
  | { event: "run_start"; data: { run_id: string; nodes: string[] } }
  | { event: "node_start"; data: { node: string } }
  | {
      event: "node_end";
      data: { node: string; stats?: Record<string, number | boolean>; completed?: number };
    }
  | { event: "error"; data: { run_id?: string; message: string } }
  | { event: "complete"; data: AnalyzeResponse };

export async function streamAnalyze(
  raw_feedback: FeedbackInput[],
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const headers = new Headers({ "Content-Type": "application/json" });
  const key = readStoredKey();
  if (key) headers.set("X-API-Key", key);

  let response: Response;
  try {
    response = await fetch(`${API_BASE}/analyze/stream`, {
      method: "POST",
      headers,
      body: JSON.stringify({ raw_feedback }),
      signal,
    });
  } catch (error) {
    if ((error as Error)?.name === "AbortError") return;
    throw new ApiError(0, `Cannot reach the API at ${API_BASE}.`);
  }

  if (response.status === 401) {
    unauthorizedHandler?.();
    throw new ApiError(401, "Your session expired. Sign in again.");
  }
  if (!response.ok) throw new ApiError(response.status, await extractError(response));
  if (!response.body) throw new ApiError(0, "The server sent no stream.");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE frames are separated by a blank line. Keep the trailing partial.
      const frames = buffer.split("\n\n");
      buffer = frames.pop() ?? "";

      for (const frame of frames) {
        let name = "";
        const dataLines: string[] = [];

        for (const line of frame.split("\n")) {
          if (line.startsWith("event:")) name = line.slice(6).trim();
          else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
        }

        if (!name || dataLines.length === 0) continue;
        try {
          onEvent({ event: name, data: JSON.parse(dataLines.join("\n")) } as StreamEvent);
        } catch {
          // A malformed frame must not kill a run that is still producing
          // good ones.
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
