const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  const body = await res.json().catch(() => null);

  if (!res.ok) {
    throw new ApiError(body?.error ?? res.statusText, res.status);
  }

  return body as T;
}

export const api = {
  register: (email: string, password: string) =>
    request<{ access_token: string; user: { id: number; email: string } }>(
      "/api/auth/register",
      { method: "POST", body: JSON.stringify({ email, password }) }
    ),
  login: (email: string, password: string) =>
    request<{ access_token: string; user: { id: number; email: string } }>(
      "/api/auth/login",
      { method: "POST", body: JSON.stringify({ email, password }) }
    ),
};
