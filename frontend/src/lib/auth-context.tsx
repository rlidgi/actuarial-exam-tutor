"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type MutableRefObject,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { api, DEFAULT_EXAM_CODE, type AuthResponse } from "./api";
import { supabaseClient } from "./supabase-client";
import { reportAdsConversion, SIGNUP_CONVERSION_LABEL } from "./gtag";

const TOKEN_STORAGE_KEY = "actuarial_tutor_token";
// Persisted alongside the token so a page refresh (not just a fresh sign-in)
// can restore it too -- see the bootstrap effect below. Without this, email
// stayed null on every visit except the one right after signing in, since
// completeSupabaseSignIn was the only place that ever set it.
const EMAIL_STORAGE_KEY = "actuarial_tutor_email";
// Same key exam-context.tsx persists the selected exam under -- read
// directly (not imported) to avoid a circular import, since ExamProvider
// itself depends on useAuth().
const EXAM_STORAGE_KEY = "actuarial_tutor_exam";
// Set right after a real sign-in completes (never on a page refresh that
// just restores an existing token from localStorage -- see
// completeSupabaseSignIn, the only place this gets set). chat/page.tsx
// reads and clears this on its next mount to start a fresh conversation,
// same as clicking "New Conversation".
export const FRESH_LOGIN_STORAGE_KEY = "actuarial_tutor_fresh_login";
// Captured from a `?ref=<code>` URL on any page (not session-only, since an
// OAuth redirect can span a real gap) and consumed exactly once, the moment
// a sign-in actually completes -- see completeSupabaseSignIn. Never applied
// retroactively to an already-signed-in user.
const REFERRAL_CODE_STORAGE_KEY = "actuarial_tutor_referral_code";

interface AuthState {
  token: string | null;
  email: string | null;
  loading: boolean;
  signInWithGoogle: () => Promise<void>;
  sendMagicLink: (email: string) => Promise<void>;
  completeSupabaseSignIn: () => Promise<void>;
  // redirectTo defaults to "/" -- callers on a protected page that want a
  // different destination (e.g. useRequireAuth's expired-session bailout)
  // pass their own.
  logout: (redirectTo?: string) => void;
  // Set synchronously the instant logout() is called, before the token
  // actually clears -- see useRequireAuth, which checks this to avoid its
  // own generic "no token -> /login" redirect racing (and winning over)
  // whatever destination logout() itself just navigated to.
  loggingOutRef: MutableRefObject<boolean>;
}

const AuthContext = createContext<AuthState | null>(null);

async function afterAuth(response: AuthResponse) {
  // A returning user who'd previously switched exams keeps that selection
  // across a fresh sign-in; a first-ever sign-in has nothing stored yet.
  const examCode = window.localStorage.getItem(EXAM_STORAGE_KEY) || DEFAULT_EXAM_CODE;
  await api.ensureProfile(response.access_token, examCode);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const loggingOutRef = useRef(false);

  useEffect(() => {
    // A one-time synchronous read from localStorage, deliberately done in
    // an effect (not a lazy useState initializer) so it never runs during
    // SSR, where window doesn't exist. There's no async boundary here for
    // these setState calls to move into -- that's the whole point, this
    // must resolve before the first client render can trust `token`.
    const stored = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    if (stored) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setToken(stored);
      const storedEmail = window.localStorage.getItem(EMAIL_STORAGE_KEY);
      if (storedEmail) {
        setEmail(storedEmail);
      }
    }
    const refCode = new URLSearchParams(window.location.search).get("ref");
    if (refCode) {
      window.localStorage.setItem(REFERRAL_CODE_STORAGE_KEY, refCode);
    }
    setLoading(false);
  }, []);

  // Both just kick off Supabase's side of the flow -- the app doesn't get
  // a token back here. Google full-page-redirects away immediately; magic
  // link emails a link. Either way, the user lands on /auth/callback,
  // which calls completeSupabaseSignIn() below.
  const signInWithGoogle = useCallback(async () => {
    const { error } = await supabaseClient.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
    if (error) throw error;
  }, []);

  const sendMagicLink = useCallback(async (magicLinkEmail: string) => {
    const { error } = await supabaseClient.auth.signInWithOtp({
      email: magicLinkEmail,
      options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
    });
    if (error) throw error;
  }, []);

  // Called from /auth/callback once supabase-js has parsed the OAuth/magic
  // -link redirect and established a Supabase session. Trades that session
  // for this app's own JWT and completes the same tail as the old login/
  // register flow (ensureProfile, localStorage, state).
  //
  // Deliberately event-driven (onAuthStateChange) rather than a one-shot
  // getSession() call: supabase-js parses the redirect's URL fragment and
  // establishes the session asynchronously, and a single getSession() can
  // resolve before that finishes, reporting no session when one is about
  // to exist a moment later. Subscribing fires immediately with whatever
  // the current state already is (INITIAL_SESSION) and then again the
  // moment the URL-derived session lands, so this can't lose that race.
  const completeSupabaseSignIn = useCallback(() => {
    return new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => {
        subscription.unsubscribe();
        reject(new Error("timed out waiting for Supabase to establish a session"));
      }, 8000);

      const {
        data: { subscription },
      } = supabaseClient.auth.onAuthStateChange((event, session) => {
        if (event !== "INITIAL_SESSION" && event !== "SIGNED_IN") return;
        if (!session) return; // INITIAL_SESSION with nothing yet -- keep waiting
        clearTimeout(timeout);
        subscription.unsubscribe();
        const referralCode = window.localStorage.getItem(REFERRAL_CODE_STORAGE_KEY);
        api
          .exchangeSupabaseToken(session.access_token, referralCode)
          .then(async (response) => {
            await afterAuth(response);
            window.localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token);
            window.localStorage.setItem(EMAIL_STORAGE_KEY, response.user.email);
            window.localStorage.removeItem(REFERRAL_CODE_STORAGE_KEY);
            window.sessionStorage.setItem(FRESH_LOGIN_STORAGE_KEY, "1");
            setToken(response.access_token);
            setEmail(response.user.email);
            // Only the exchange call that actually created the account
            // reports is_new_user -- a returning login must never re-fire
            // this, or Google Ads would count every login as a new signup.
            if (response.is_new_user) {
              reportAdsConversion(SIGNUP_CONVERSION_LABEL, response.user.email);
            }
            resolve();
          })
          .catch(reject);
      });
    });
  }, []);

  const logout = useCallback(
    (redirectTo: string = "/") => {
      loggingOutRef.current = true;
      // Fire-and-forget, using the token before it's cleared below -- purely
      // for the admin activity dashboard (see api.ts's logout), never
      // something the actual sign-out should wait on or fail because of.
      if (token) void api.logout(token).catch(() => {});
      window.localStorage.removeItem(TOKEN_STORAGE_KEY);
      window.localStorage.removeItem(EMAIL_STORAGE_KEY);
      setToken(null);
      setEmail(null);
      // Otherwise a lingering Supabase-side session could silently
      // re-authenticate the next time this user lands on /auth/callback.
      void supabaseClient.auth.signOut();
      router.push(redirectTo);
    },
    [router, token]
  );

  return (
    <AuthContext.Provider
      value={{
        token,
        email,
        loading,
        signInWithGoogle,
        sendMagicLink,
        completeSupabaseSignIn,
        logout,
        loggingOutRef,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
