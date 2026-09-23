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

export interface ChatStreamEvent {
  delta?: string;
  done?: boolean;
  // Set instead of delta/done when the caller is out of free-trial turns
  // and isn't subscribed -- see entitlement_service.chat_access_status.
  // Arrives as a single plain-JSON response (never a stream), same as any
  // other blocked turn -- see chat.py's _access_gate.
  blocked?: "trial_exhausted";
}

// POST /api/chat/message and /regenerate stream their reply as
// Server-Sent Events (see chat.py's _run_tutor_turn) so the tutor's answer
// can render as it's generated instead of waiting for the whole thing.
// An async generator, not request<T>() -- the response body is a sequence
// of `data: {...}\n\n` frames, not one JSON value.
async function* streamRequest(
  path: string,
  options: RequestInit,
  token: string
): AsyncGenerator<ChatStreamEvent> {
  const isFormData = options.body instanceof FormData;
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(body?.error ?? res.statusText, res.status);
  }

  // A blocked turn short-circuits before the tutor ever runs, so it's a
  // plain JSON response ({blocked: "trial_exhausted"}), not a stream.
  if (!(res.headers.get("content-type") ?? "").includes("text/event-stream")) {
    const body = await res.json().catch(() => null);
    if (body) yield body as ChatStreamEvent;
    return;
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let boundary: number;
    while ((boundary = buffer.indexOf("\n\n")) !== -1) {
      const rawEvent = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      if (rawEvent.startsWith("data: ")) {
        yield JSON.parse(rawEvent.slice("data: ".length)) as ChatStreamEvent;
      }
    }
  }
}

export interface AuthResponse {
  access_token: string;
  user: { id: number; email: string };
  // True only for the exchange call that actually created the account --
  // see user_service.find_or_create_by_external_identity. Drives the
  // Google Ads "Sign-up" conversion (see auth-context.tsx) so a returning
  // login never fires it again.
  is_new_user: boolean;
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

export interface ReferralRewardDTO {
  reward_type: "referred_percent_off" | "referrer_credit";
  status: "pending" | "applied" | "failed";
  created_at: string | null;
  applied_at: string | null;
}

export interface ReferralSummary {
  referral_code: string;
  referral_url: string;
  completed_referral_count: number;
  rewards: ReferralRewardDTO[];
}

// Must match backend/app/models/feedback.py's CATEGORIES tuple.
export type FeedbackCategory = "bug" | "feature_request" | "ui_ux" | "performance" | "other";

// Every field optional -- see api/feedback.py, a submission with just one
// rating (or just a message) is still valid.
export interface FeedbackSubmission {
  overall_rating?: number | null;
  overall_detail?: string | null;
  tutor_quality_rating?: number | null;
  tutor_quality_detail?: string | null;
  ease_of_use_rating?: number | null;
  ease_of_use_detail?: string | null;
  value_rating?: number | null;
  value_detail?: string | null;
  category?: FeedbackCategory | null;
  message?: string | null;
}

export interface AdminUserDTO {
  id: number;
  email: string;
  created_at: string | null;
  last_login_at: string | null;
  last_logout_at: string | null;
}

export const api = {
  exchangeSupabaseToken: (supabaseAccessToken: string, referralCode?: string | null) =>
    request<AuthResponse>("/api/auth/exchange", {
      method: "POST",
      body: JSON.stringify({
        supabase_access_token: supabaseAccessToken,
        ...(referralCode ? { referral_code: referralCode } : {}),
      }),
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
      return streamRequest("/api/chat/message", { method: "POST", body: formData }, token);
    }
    return streamRequest(
      "/api/chat/message",
      { method: "POST", body: JSON.stringify({ exam_code: examCode, message }) },
      token
    );
  },
  regenerate: (token: string, examCode: string, editedMessage?: string) =>
    streamRequest(
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
  getReferralSummary: (token: string) =>
    request<ReferralSummary>("/api/referrals", {}, token),
  // `website` is a honeypot field -- always sent empty by the real form,
  // see contact-content.tsx. Never surfaced to the visitor.
  submitContact: (name: string, email: string, message: string, website: string = "") =>
    request<{ ok: boolean }>("/api/contact", {
      method: "POST",
      body: JSON.stringify({ name, email, message, website }),
    }),
  submitFeedback: (token: string, submission: FeedbackSubmission) =>
    request<{ ok: boolean }>(
      "/api/feedback",
      { method: "POST", body: JSON.stringify(submission) },
      token
    ),
  // Records a logout event for the admin dashboard -- see auth-context.tsx's
  // logout(), the only caller. Purely observability; callers don't need to
  // treat a failure here as blocking the actual sign-out.
  logout: (token: string) => request<{ ok: boolean }>("/api/auth/logout", { method: "POST" }, token),
  adminListUsers: (token: string) =>
    request<{ users: AdminUserDTO[] }>("/api/admin/users", {}, token),
  // Bypasses request() -- the manual is served as raw text/html, not JSON,
  // so there's no body to parse as an ApiError-shaped object on failure.
  // Public: the study manual needs no token, same as the backend route.
  getCourseHtml: async (examCode: string): Promise<string> => {
    const res = await fetch(`${API_URL}/api/courses/${examCode}`);
    if (!res.ok) {
      throw new ApiError(res.statusText, res.status);
    }
    return res.text();
  },
  // Same treatment as getCourseHtml -- raw text/html, not JSON, and public.
  getFormulaSheetHtml: async (examCode: string): Promise<string> => {
    const res = await fetch(`${API_URL}/api/formulas/${examCode}`);
    if (!res.ok) {
      throw new ApiError(res.statusText, res.status);
    }
    return res.text();
  },
};
