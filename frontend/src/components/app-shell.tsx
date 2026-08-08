"use client";

import { useEffect, useState, type ReactNode } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useChatView } from "@/lib/chat-view-context";
import { api, EXAM_CODE, type ExamInfo } from "@/lib/api";

function formatDayLabel(iso: string): string {
  // iso is a plain YYYY-MM-DD from the backend (UTC calendar date) --
  // parsed as UTC too so the label doesn't shift a day depending on the
  // viewer's own timezone offset from UTC.
  const date = new Date(`${iso}T00:00:00Z`);
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}

export function AppShell({ children }: { children: ReactNode }) {
  const { token, email, logout, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const { selectedDate, setSelectedDate, startNewConversation, historyDaysVersion } =
    useChatView();

  const [exams, setExams] = useState<ExamInfo[]>([]);
  const [days, setDays] = useState<string[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    api.getExams().then((r) => setExams(r.exams)).catch(() => {});
  }, []);

  useEffect(() => {
    if (!token) return;
    api.getHistoryDays(token).then((r) => setDays(r.days)).catch(() => {});
  }, [token, historyDaysVersion]);

  const goToChat = () => {
    setSidebarOpen(false);
    if (pathname !== "/chat") router.push("/chat");
  };

  const handleNewConversation = () => {
    startNewConversation();
    goToChat();
  };

  const handleSelectDay = (day: string) => {
    setSelectedDate(day);
    goToChat();
  };

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <div className="flex h-dvh overflow-hidden bg-paper text-ink">
      <button
        type="button"
        aria-label="Open menu"
        aria-expanded={sidebarOpen}
        onClick={() => setSidebarOpen(true)}
        className="fixed left-3 top-3 z-40 flex h-9 w-9 items-center justify-center rounded-md border border-rule bg-paper-raised text-lg shadow-md md:hidden"
      >
        &#9776;
      </button>
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 max-w-[82vw] flex-shrink-0 transform flex-col gap-2 overflow-hidden bg-ink p-3 text-paper transition-transform duration-200 md:static md:w-64 md:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex flex-col gap-2 border-b border-white/10 pb-3">
          <Link
            href="/chat"
            onClick={() => setSidebarOpen(false)}
            className="inline-flex items-center gap-2 self-start rounded-md bg-paper px-2 py-1"
          >
            <Image src="/logo-mark.png" alt="" width={20} height={20} className="h-5 w-auto" />
            <span className="h-4 w-px bg-rule" />
            <Image
              src="/logo-text.png"
              alt="Actuarial Exams Tutor"
              width={120}
              height={14}
              className="h-3.5 w-auto"
            />
          </Link>
          <select
            value={EXAM_CODE}
            onChange={() => {}}
            className="w-full rounded border border-white/20 bg-white/5 px-2 py-1.5 text-sm text-paper"
          >
            {exams.map((e) => (
              <option key={e.code} value={e.code} className="text-ink">
                {e.name}
              </option>
            ))}
          </select>
        </div>

        <nav className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto py-2">
          {days.length === 0 && (
            <p className="px-2 py-1 text-xs text-paper/50">No conversations yet.</p>
          )}
          {days.map((day) => (
            <button
              key={day}
              type="button"
              onClick={() => handleSelectDay(day)}
              className={`rounded px-2 py-1.5 text-left text-sm ${
                selectedDate === day
                  ? "bg-ledger-bright/20 font-semibold text-paper"
                  : "text-paper/75 hover:bg-white/5"
              }`}
            >
              {formatDayLabel(day)}
            </button>
          ))}
        </nav>

        <div className="flex flex-col gap-2 border-t border-white/10 pt-3">
          <button
            type="button"
            onClick={handleNewConversation}
            className="rounded-md bg-ledger px-3 py-2 text-center text-sm font-semibold text-paper hover:bg-ledger-bright"
          >
            New Conversation
          </button>
          <Link
            href="/progress"
            onClick={() => setSidebarOpen(false)}
            className="rounded-md border border-white/20 px-3 py-2 text-center text-sm text-paper/80 hover:border-ledger-bright hover:text-ledger-bright"
          >
            Proficiency Dashboard
          </Link>

          {!loading && (
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 px-1 pt-1 text-xs text-paper/50">
              {email && <span>{email}</span>}
              <button type="button" onClick={handleLogout} className="hover:text-ledger-bright">
                Sign out
              </button>
            </div>
          )}
        </div>
      </aside>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">{children}</div>
    </div>
  );
}
