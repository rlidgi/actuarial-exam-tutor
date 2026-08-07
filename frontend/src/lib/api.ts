const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";

export const EXAM_CODE = "P";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

// Flask-JWT-Extended returns 401 for a validly-formed but expired/invalid
// token, and 422 for one it can't even decode (e.g. corrupted storage).
// Either way the stored token is unusable and the user needs to re-login.
export function isAuthError(err: unknown): err is ApiError {
  return err instanceof ApiError && (err.status === 401 || err.status === 422);
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  const body = await res.json().catch(() => null);

  if (!res.ok) {
    throw new ApiError(body?.error ?? res.statusText, res.status);
  }

  return body as T;
}

export interface AuthResponse {
  access_token: string;
  user: { id: number; email: string };
}

export interface ChatResponse {
  session_id: number;
  reply: string;
}

export interface TopicProgress {
  name: string;
  mastery: number | null;
  difficulty: number | null;
}

export interface CategoryProgress {
  name: string;
  exam_weight: number | null;
  topics: TopicProgress[];
}

export interface ProgressSummary {
  overall_mastery: number;
  topics_studied: number;
  topics_total: number;
  weakest_topic: string | null;
  weakest_topic_mastery: number | null;
  open_mistakes: number;
  last_session_at: string | null;
  next_recommended_topic: string;
  next_recommended_reason: string;
  categories: CategoryProgress[];
}

export interface SessionSummary {
  id: number;
  started_at: string | null;
  ended_at: string | null;
  summary: string | null;
}

export const api = {
  register: (email: string, password: string) =>
    request<AuthResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  login: (email: string, password: string) =>
    request<AuthResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  ensureProfile: (token: string) =>
    request<{ id: number; exam: string }>(
      "/api/students/profiles",
      { method: "POST", body: JSON.stringify({ exam_code: EXAM_CODE }) },
      token
    ),
  sendMessage: (token: string, message: string) =>
    request<ChatResponse>(
      "/api/chat/message",
      { method: "POST", body: JSON.stringify({ exam_code: EXAM_CODE, message }) },
      token
    ),
  getProgress: (token: string) =>
    request<ProgressSummary>(`/api/students/me/progress?exam=${EXAM_CODE}`, {}, token),
  getSessions: (token: string) =>
    request<{ sessions: SessionSummary[] }>(
      `/api/students/me/sessions?exam=${EXAM_CODE}`,
      {},
      token
    ),
};
