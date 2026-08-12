const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";

// Only a fallback for contexts with no signed-in "current exam" concept yet
// (exam-context.tsx's initial value before it resolves; pricing/page.tsx's
// own independent, unrelated display logic). Every authenticated call below
// takes examCode as a required parameter instead of defaulting to this --
// see frontend exam switcher plan for why silent defaulting was the bug.
export const DEFAULT_EXAM_CODE = "P";

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

export interface OpenChatResponse {
  messages: ChatMessageDTO[];
}

export interface RestartChatResponse {
  message?: ChatMessageDTO;
  // Set instead of message when the caller is out of free-trial turns and
  // isn't subscribed -- see entitlement_service.chat_access_status.
  blocked?: "trial_exhausted";
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
  exchangeSupabaseToken: (supabaseAccessToken: string) =>
    request<AuthResponse>("/api/auth/exchange", {
      method: "POST",
      body: JSON.stringify({ supabase_access_token: supabaseAccessToken }),
    }),
  ensureProfile: (token: string, examCode: string) =>
    request<{ id: number; exam: string }>(
      "/api/students/profiles",
      { method: "POST", body: JSON.stringify({ exam_code: examCode }) },
      token
    ),
  sendMessage: (token: string, examCode: string, message: string, image?: File) => {
    if (image) {
      const formData = new FormData();
      formData.set("exam_code", examCode);
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
      { method: "POST", body: JSON.stringify({ exam_code: examCode, message }) },
      token
    );
  },
  regenerate: (token: string, examCode: string, editedMessage?: string) =>
    request<ChatResponse>(
      "/api/chat/regenerate",
      {
        method: "POST",
        body: JSON.stringify({ exam_code: examCode, edited_message: editedMessage }),
      },
      token
    ),
  openChat: (token: string, examCode: string) =>
    request<OpenChatResponse>(`/api/chat/open?exam=${examCode}`, { method: "POST" }, token),
  restartChat: (token: string, examCode: string) =>
    request<RestartChatResponse>(`/api/chat/restart?exam=${examCode}`, { method: "POST" }, token),
  getProgress: (token: string, examCode: string) =>
    request<ProgressSummary>(`/api/students/me/progress?exam=${examCode}`, {}, token),
  getSessions: (token: string, examCode: string) =>
    request<{ sessions: SessionSummary[] }>(
      `/api/students/me/sessions?exam=${examCode}`,
      {},
      token
    ),
  getExams: () => request<{ exams: ExamInfo[] }>("/api/exams"),
  getHistoryDays: (token: string, examCode: string) =>
    request<{ days: string[] }>(`/api/chat/history/days?exam=${examCode}`, {}, token),
  getHistoryDay: (token: string, examCode: string, date: string) =>
    request<{ messages: ChatMessageDTO[] }>(
      `/api/chat/history/day/${date}?exam=${examCode}`,
      {},
      token
    ),
  getBillingStatus: (token: string, examCode: string) =>
    request<BillingStatus>(`/api/billing/status?exam=${examCode}`, {}, token),
  createCheckoutSession: (token: string, examCode: string) =>
    request<{ url: string }>(
      "/api/billing/checkout",
      { method: "POST", body: JSON.stringify({ exam_code: examCode }) },
      token
    ),
  createPortalSession: (token: string, examCode: string) =>
    request<{ url: string }>(
      "/api/billing/portal",
      { method: "POST", body: JSON.stringify({ exam_code: examCode }) },
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
  getCourseHtml: async (token: string, examCode: string): Promise<string> => {
    const res = await fetch(`${API_URL}/api/courses/${examCode}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      throw new ApiError(res.statusText, res.status);
    }
    return res.text();
  },
};
