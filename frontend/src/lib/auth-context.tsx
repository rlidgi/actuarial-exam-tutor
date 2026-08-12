"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api, DEFAULT_EXAM_CODE, type AuthResponse } from "./api";
import { supabaseClient } from "./supabase-client";

const TOKEN_STORAGE_KEY = "actuarial_tutor_token";
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

interface AuthState {
  token: string | null;
  email: string | null;
  loading: boolean;
  signInWithGoogle: () => Promise<void>;
  sendMagicLink: (email: string) => Promise<void>;
  completeSupabaseSignIn: () => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

async function afterAuth(response: AuthResponse) {
  // A returning user who'd previously switched exams keeps that selection
  // across a fresh sign-in; a first-ever sign-in has nothing stored yet.
  const examCode = window.localStorage.getItem(EXAM_STORAGE_KEY) || DEFAULT_EXAM_CODE;
  await api.ensureProfile(response.access_token, examCode);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

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
        api
          .exchangeSupabaseToken(session.access_token)
          .then(async (response) => {
            await afterAuth(response);
            window.localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token);
            window.sessionStorage.setItem(FRESH_LOGIN_STORAGE_KEY, "1");
            setToken(response.access_token);
            setEmail(response.user.email);
            resolve();
          })
          .catch(reject);
      });
    });
  }, []);

  const logout = useCallback(() => {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setEmail(null);
    // Otherwise a lingering Supabase-side session could silently
    // re-authenticate the next time this user lands on /auth/callback.
    void supabaseClient.auth.signOut();
  }, []);

  return (
    <AuthContext.Provider
      value={{ token, email, loading, signInWithGoogle, sendMagicLink, completeSupabaseSignIn, logout }}
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
