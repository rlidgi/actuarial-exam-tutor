"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError, isAuthError, type AdminUserDTO } from "@/lib/api";

// Client-side only, for UX (redirect non-admins away without a flash of
// the page) -- the real gate is server-side, ADMIN_EMAILS in
// backend/app/config.py, checked on every /api/admin/* request.
const ADMIN_EMAIL = "yaronyaronlid@gmail.com";

function formatDateTime(iso: string | null): string {
  if (!iso) return "Never";
  return new Date(iso).toLocaleString();
}

export default function AdminPage() {
  const { token, email, loading } = useAuth();
  const router = useRouter();
  const [users, setUsers] = useState<AdminUserDTO[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (loading) return;
    if (!token) {
      router.push("/login");
      return;
    }
    if (email && email !== ADMIN_EMAIL) {
      router.push("/chat");
    }
  }, [loading, token, email, router]);

  useEffect(() => {
    if (!token || email !== ADMIN_EMAIL) return;
    api
      .adminListUsers(token)
      .then((r) => setUsers(r.users))
      .catch((err) => {
        if (isAuthError(err)) {
          router.push("/login");
          return;
        }
        setError(err instanceof ApiError ? err.message : "Failed to load users.");
      });
  }, [token, email, router]);

  if (loading || !token || email !== ADMIN_EMAIL) {
    return null;
  }

  return (
    <div className="min-h-dvh w-full bg-paper text-ink">
      <div className="mx-auto max-w-4xl px-4 py-6 sm:px-6">
        <Link href="/chat" className="btn mb-4 inline-block">
          &larr; Back to Tutor
        </Link>

        <h1 className="mb-1 text-2xl font-bold text-ink">Admin</h1>
        <p className="mb-6 text-sm text-pencil">Registered users and their login activity.</p>

        {error && <div className="banner warn mb-4">{error}</div>}

        {!users && !error && <p className="text-sm text-pencil">Loading...</p>}

        {users && (
          <div className="overflow-x-auto rounded-lg border border-rule">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-rule bg-paper-raised text-xs uppercase tracking-wide text-pencil">
                  <th className="px-4 py-2 font-medium">Email</th>
                  <th className="px-4 py-2 font-medium">Signed up</th>
                  <th className="px-4 py-2 font-medium">Last login</th>
                  <th className="px-4 py-2 font-medium">Last logout</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b border-rule last:border-0">
                    <td className="px-4 py-2 text-ink">{u.email}</td>
                    <td className="px-4 py-2 text-pencil">{formatDateTime(u.created_at)}</td>
                    <td className="px-4 py-2 text-pencil">{formatDateTime(u.last_login_at)}</td>
                    <td className="px-4 py-2 text-pencil">{formatDateTime(u.last_logout_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
