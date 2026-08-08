"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api, type AuthResponse } from "./api";
import { supabaseClient } from "./supabase-client";

const TOKEN_STORAGE_KEY = "actuarial_tutor_token";

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
  await api.ensureProfile(response.access_token);
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
  const completeSupabaseSignIn = useCallback(async () => {
    const { data, error } = await supabaseClient.auth.getSession();
    if (error || !data.session) {
      throw error ?? new Error("no Supabase session to complete sign-in with");
    }
    const response = await api.exchangeSupabaseToken(data.session.access_token);
    await afterAuth(response);
    window.localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token);
    setToken(response.access_token);
    setEmail(response.user.email);
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
