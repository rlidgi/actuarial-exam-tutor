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
  // FormData bodies (image uploads) need the browser to set their own
  // multipart boundary header -- forcing application/json here would break
  // that, so only default to JSON when the body isn't already FormData.
  const isFormData = options.body instanceof FormData;

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
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
  session_id?: number;
  reply?: string;
  // Set instead of session_id/reply when the caller is out of free-trial
  // turns and isn't subscribed -- see entitlement_service.chat_access_status.
  blocked?: "trial_exhausted";
}

export interface BillingStatus {
  subscribed: boolean;
  free_turns_remaining: number;
  free_trial_total: number;
}

export interface ChatMessageDTO {
  role: "user" | "assistant";
  content: string;
}

export interface ExamInfo {
  code: string;
  name: string;
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
  sendMessage: (token: string, message: string, image?: File) => {
    if (image) {
      const formData = new FormData();
      formData.set("exam_code", EXAM_CODE);
      formData.set("message", message);
      formData.set("image", image);
      return request<ChatResponse>(
        "/api/chat/message",
        { method: "POST", body: formData },
        token
      );
    }
    return request<ChatResponse>(
      "/api/chat/message",
      { method: "POST", body: JSON.stringify({ exam_code: EXAM_CODE, message }) },
      token
    );
  },
  regenerate: (token: string, editedMessage?: string) =>
    request<ChatResponse>(
      "/api/chat/regenerate",
      {
        method: "POST",
        body: JSON.stringify({ exam_code: EXAM_CODE, edited_message: editedMessage }),
      },
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
  getExams: () => request<{ exams: ExamInfo[] }>("/api/exams"),
  getHistoryDays: (token: string) =>
    request<{ days: string[] }>(`/api/chat/history/days?exam=${EXAM_CODE}`, {}, token),
  getHistoryDay: (token: string, date: string) =>
    request<{ messages: ChatMessageDTO[] }>(
      `/api/chat/history/day/${date}?exam=${EXAM_CODE}`,
      {},
      token
    ),
  getBillingStatus: (token: string) =>
    request<BillingStatus>(`/api/billing/status?exam=${EXAM_CODE}`, {}, token),
  createCheckoutSession: (token: string, examCode: string = EXAM_CODE) =>
    request<{ url: string }>(
      "/api/billing/checkout",
      { method: "POST", body: JSON.stringify({ exam_code: examCode }) },
      token
    ),
  createPortalSession: (token: string) =>
    request<{ url: string }>(
      "/api/billing/portal",
      { method: "POST", body: JSON.stringify({ exam_code: EXAM_CODE }) },
      token
    ),
  syncCheckoutSession: (token: string, sessionId: string) =>
    request<{ ok: boolean }>(
      "/api/billing/sync",
      { method: "POST", body: JSON.stringify({ session_id: sessionId }) },
      token
    ),
  // Bypasses request() -- the manual is served as raw text/html, not JSON,
  // so there's no body to parse as an ApiError-shaped object on failure.
  getCourseHtml: async (token: string, examCode: string = EXAM_CODE): Promise<string> => {
    const res = await fetch(`${API_URL}/api/courses/${examCode}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      throw new ApiError(res.statusText, res.status);
    }
    return res.text();
  },
};
