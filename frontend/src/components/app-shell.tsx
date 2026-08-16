"use client";

import { useEffect, useState, type ReactNode } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useChatView } from "@/lib/chat-view-context";
import { useExam } from "@/lib/exam-context";
import { useBillingStatus } from "@/lib/use-billing-status";
import { api } from "@/lib/api";

// Persisted like every other cross-visit UI preference in this app (see
// TOKEN_STORAGE_KEY etc. in auth-context.tsx) -- same "actuarial_tutor_"
// prefix, one-time synchronous read in an effect so it never runs during
// SSR (window doesn't exist there).
const SIDEBAR_COLLAPSED_STORAGE_KEY = "actuarial_tutor_sidebar_collapsed";

// Small line-style icons in the common SaaS-sidebar idiom (ChatGPT, Linear,
// etc.) -- 24x24 viewBox, single-color stroke via currentColor so each
// picks up whatever text color its row is given, no per-icon color props
// needed. Colocated here rather than split into their own module since
// nothing outside this sidebar uses them (same reasoning as sign-in-modal's
// local GoogleIcon).
function IconArrowsLeftRight() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="8 7 3 12 8 17" />
      <polyline points="16 7 21 12 16 17" />
    </svg>
  );
}
function IconCompose() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 20h4L18.5 9.5a2.1 2.1 0 0 0-3-3L5 17v3Z" />
    </svg>
  );
}
function IconChartBar() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <line x1="5" y1="20" x2="5" y2="12" />
      <line x1="12" y1="20" x2="12" y2="6" />
      <line x1="19" y1="20" x2="19" y2="15" />
    </svg>
  );
}
function IconGift() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="4" y="9" width="16" height="11" rx="1" />
      <line x1="4" y1="13" x2="20" y2="13" />
      <line x1="12" y1="9" x2="12" y2="20" />
      <path d="M12 9C10 6 7 6 7 8.5S9.5 9 12 9Z" />
      <path d="M12 9c2-3 5-3 5-.5S14.5 9 12 9Z" />
    </svg>
  );
}
function IconBook() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 5.5C4 4.7 4.7 4 5.5 4H12v16H5.5c-.8 0-1.5-.7-1.5-1.5v-13Z" />
      <path d="M20 5.5C20 4.7 19.3 4 18.5 4H12v16h6.5c.8 0 1.5-.7 1.5-1.5v-13Z" />
    </svg>
  );
}
function IconDocument() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M6 3h8l4 4v14H6V3Z" />
      <path d="M14 3v4h4" />
      <line x1="8.5" y1="12" x2="15.5" y2="12" />
      <line x1="8.5" y1="16" x2="15.5" y2="16" />
    </svg>
  );
}
function IconMessage() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 5.5C4 4.7 4.7 4 5.5 4h13c.8 0 1.5.7 1.5 1.5v10c0 .8-.7 1.5-1.5 1.5H9l-4 3.5v-3.5H5.5C4.7 17 4 16.3 4 15.5v-10Z" />
    </svg>
  );
}
function IconCard() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="5.5" width="18" height="13" rx="1.8" />
      <line x1="3" y1="10" x2="21" y2="10" />
      <line x1="6" y1="14.5" x2="10" y2="14.5" />
    </svg>
  );
}
function IconLogout() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M9 4H6.5A1.5 1.5 0 0 0 5 5.5v13A1.5 1.5 0 0 0 6.5 20H9" />
      <line x1="20" y1="12" x2="10.5" y2="12" />
      <path d="m16.5 8 4 4-4 4" />
    </svg>
  );
}

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

// One row in the primary nav list (New Conversation, Dashboard, Referrals,
// etc.) -- uniform icon+label treatment matching every row in that list,
// same idiom as ChatGPT's own sidebar ("New chat", "Projects", ... all
// styled identically). `collapsed` hides the label at md+ only (desktop
// rail mode); mobile's slide-over drawer always shows labels regardless,
// since the collapse toggle itself is desktop-only -- see the button below.
function NavRow({
  active,
  collapsed,
  icon,
  label,
  ...rest
}: {
  active?: boolean;
  collapsed: boolean;
  icon: ReactNode;
  label: string;
} & (
  | { href: string; onClick?: () => void }
  | { href?: undefined; onClick: () => void }
)) {
  const className = `flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm ${
    collapsed ? "md:justify-center md:px-2" : ""
  } ${
    active
      ? "bg-white/10 font-semibold text-paper"
      : "text-paper/80 hover:bg-white/5 hover:text-paper"
  }`;
  const content = (
    <>
      <span className="flex-shrink-0">{icon}</span>
      <span className={collapsed ? "md:hidden" : ""}>{label}</span>
    </>
  );

  if ("href" in rest && rest.href) {
    return (
      <Link href={rest.href} onClick={rest.onClick} className={className} title={label}>
        {content}
      </Link>
    );
  }
  return (
    <button type="button" onClick={rest.onClick} className={className} title={label}>
      {content}
    </button>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const { token, email, logout, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const { selectedDate, setSelectedDate, startNewConversation, historyDaysVersion } =
    useChatView();
  const { examCode, exams, loading: examsLoading, setExamCode } = useExam();
  const { status: billingStatus } = useBillingStatus(token, examCode);

  const [days, setDays] = useState<string[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [switching, setSwitching] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    if (!token) return;
    api.getHistoryDays(token, examCode).then((r) => setDays(r.days)).catch(() => {});
  }, [token, examCode, historyDaysVersion]);

  useEffect(() => {
    // Desktop-only preference (see the toggle button, hidden below md) --
    // a one-time synchronous read, same pattern/reasoning as auth-context's
    // token restore: must resolve before rendering commits to a width, and
    // there's no async boundary for it to move into.
    const stored = window.localStorage.getItem(SIDEBAR_COLLAPSED_STORAGE_KEY);
    if (stored === "1") {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setCollapsed(true);
    }
  }, []);

  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      const next = !prev;
      window.localStorage.setItem(SIDEBAR_COLLAPSED_STORAGE_KEY, next ? "1" : "0");
      return next;
    });
  };

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
  };

  const handleSelectExam = async (code: string) => {
    if (code === examCode || switching) return;
    setSwitching(true);
    try {
      await setExamCode(code);
      // The previous exam's live conversation doesn't belong to the newly
      // selected one -- start fresh, same as the sidebar's own button.
      startNewConversation();
      goToChat();
    } catch {
      // Leave the dropdown showing the still-current exam rather than a
      // switch that silently didn't take effect.
    } finally {
      setSwitching(false);
    }
  };

  const handleManageSubscription = async () => {
    if (!token) return;
    try {
      const { url } = await api.createPortalSession(token, examCode);
      window.location.href = url;
    } catch {
      // No billing account yet (shouldn't normally happen since this
      // button only shows once billingStatus.subscribed is true) --
      // fall back to the subscribe page rather than a dead click.
      router.push(`/subscribe?exam=${examCode}`);
    }
  };

  const closeMobileSidebar = () => setSidebarOpen(false);

  return (
    <div className="flex h-dvh overflow-hidden bg-paper text-ink">
      <button
        type="button"
        aria-label="Open menu"
        aria-expanded={sidebarOpen}
        onClick={() => setSidebarOpen(true)}
        className="fixed right-3 top-3 z-40 flex h-9 w-9 items-center justify-center rounded-md border border-rule bg-paper-raised text-lg shadow-md md:hidden"
      >
        &#9776;
      </button>
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
          onClick={closeMobileSidebar}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 max-w-[82vw] flex-shrink-0 transform flex-col overflow-hidden bg-ink p-3 text-paper transition-transform duration-200 md:static md:translate-x-0 md:transition-[width] ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } ${collapsed ? "md:w-16" : "md:w-64"}`}
      >
        <div className="border-b border-white/10 pb-3">
          {/* Expanded (and always on mobile, regardless of `collapsed` --
              same md:-only gating as everywhere else in this sidebar):
              full wordmark + a separate collapse-toggle button. */}
          <div className={`flex items-center justify-between gap-2 ${collapsed ? "md:hidden" : ""}`}>
            <Link
              href="/"
              onClick={closeMobileSidebar}
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
            <button
              type="button"
              onClick={toggleCollapsed}
              aria-label="Collapse sidebar"
              title="Collapse sidebar"
              className="hidden flex-shrink-0 rounded-md p-1.5 text-paper/60 hover:bg-white/5 hover:text-paper md:inline-flex"
            >
              <IconArrowsLeftRight />
            </button>
          </div>

          {/* Collapsed rail: one slot instead of two side by side (that's
              what overflowed the 64px rail before) -- shows the brand mark
              by default, swaps to the expand icon on hover, same idiom
              ChatGPT's own collapsed sidebar uses for its top icon. */}
          <button
            type="button"
            onClick={toggleCollapsed}
            aria-label="Expand sidebar"
            title="Expand sidebar"
            className={`group hidden h-8 w-8 items-center justify-center rounded-md hover:bg-white/5 ${
              collapsed ? "md:flex" : ""
            }`}
          >
            {/* Plain <img>, not next/image: two different next/image-
                optimized assets here both rendered blank in the browser
                (worked fine server-side via curl) despite matching every
                other next/image usage in this file -- next/image's
                automatic AVIF/WebP negotiation is the prime suspect, so
                this one skips that pipeline and fetches the file as-is. */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/favicon-mark.jpg"
              alt=""
              width={20}
              height={20}
              className="h-5 w-5 rounded group-hover:hidden"
            />
            <span className="hidden text-paper/60 group-hover:flex">
              <IconArrowsLeftRight />
            </span>
          </button>
        </div>

        <div className={`pt-3 ${collapsed ? "md:hidden" : ""}`}>
          <select
            value={examCode}
            onChange={(e) => handleSelectExam(e.target.value)}
            disabled={examsLoading || switching}
            className="w-full rounded border border-white/20 bg-white/5 px-2 py-1.5 text-sm text-paper disabled:opacity-50"
          >
            {exams.map((e) => (
              <option key={e.code} value={e.code} className="text-ink">
                {e.name}
              </option>
            ))}
          </select>
        </div>

        <nav className="flex flex-col gap-0.5 pt-3">
          <NavRow
            collapsed={collapsed}
            icon={<IconCompose />}
            label="New Conversation"
            onClick={handleNewConversation}
          />
          <NavRow
            collapsed={collapsed}
            icon={<IconChartBar />}
            label="Proficiency Dashboard"
            href="/progress"
            onClick={closeMobileSidebar}
            active={pathname === "/progress"}
          />
          <NavRow
            collapsed={collapsed}
            icon={<IconGift />}
            label="Referrals"
            href="/account"
            onClick={closeMobileSidebar}
            active={pathname === "/account"}
          />
          <NavRow
            collapsed={collapsed}
            icon={<IconBook />}
            label="Study Manual"
            href="/manual"
            onClick={closeMobileSidebar}
            active={pathname === "/manual"}
          />
          <NavRow
            collapsed={collapsed}
            icon={<IconDocument />}
            label="Formula Sheet"
            href="/formulas"
            onClick={closeMobileSidebar}
            active={pathname === "/formulas"}
          />
          <NavRow
            collapsed={collapsed}
            icon={<IconMessage />}
            label="Feedback"
            href="/feedback"
            onClick={closeMobileSidebar}
            active={pathname === "/feedback"}
          />
          {billingStatus &&
            (billingStatus.subscribed ? (
              <NavRow
                collapsed={collapsed}
                icon={<IconCard />}
                label="Manage subscription"
                onClick={handleManageSubscription}
              />
            ) : (
              <NavRow
                collapsed={collapsed}
                icon={<IconCard />}
                label="Subscribe"
                href={`/subscribe?exam=${examCode}`}
                onClick={closeMobileSidebar}
                active={pathname === "/subscribe"}
              />
            ))}
        </nav>

        <div className={`mt-3 flex min-h-0 flex-1 flex-col border-t border-white/10 pt-3 ${collapsed ? "md:hidden" : ""}`}>
          <span className="px-2.5 pb-1 text-xs font-medium uppercase tracking-wide text-paper/40">
            History
          </span>
          <div className="flex min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto">
            {days.length === 0 && (
              <p className="px-2.5 py-1 text-xs text-paper/50">No conversations yet.</p>
            )}
            {days.map((day) => (
              <button
                key={day}
                type="button"
                onClick={() => handleSelectDay(day)}
                className={`flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-left text-sm ${
                  selectedDate === day
                    ? "bg-ledger-bright/20 font-semibold text-paper"
                    : "text-paper/75 hover:bg-white/5"
                }`}
              >
                <span className="flex-shrink-0 text-paper/50">
                  <IconMessage />
                </span>
                {formatDayLabel(day)}
              </button>
            ))}
          </div>
        </div>

        {!loading && (
          <div
            className={`mt-auto flex items-center gap-2 border-t border-white/10 pt-3 ${
              collapsed ? "md:flex-col md:gap-1.5" : ""
            }`}
          >
            <div
              className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-ledger-bright/30 text-xs font-semibold text-paper"
              title={email ?? undefined}
            >
              {(email ?? "?").charAt(0).toUpperCase()}
            </div>
            {email && (
              <span className={`min-w-0 flex-1 truncate text-xs text-paper/60 ${collapsed ? "md:hidden" : ""}`}>
                {email}
              </span>
            )}
            <button
              type="button"
              onClick={handleLogout}
              aria-label="Sign out"
              title="Sign out"
              className="flex-shrink-0 rounded-md p-1.5 text-paper/60 hover:bg-white/5 hover:text-paper"
            >
              <IconLogout />
            </button>
          </div>
        )}
      </aside>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">{children}</div>
    </div>
  );
}
