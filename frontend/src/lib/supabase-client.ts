import { createClient } from "@supabase/supabase-js";

// The ONLY place in the frontend that talks to Supabase directly -- Google
// OAuth and magic-link sign-in both go through this client (see
// components/sign-in-modal.tsx and app/auth/callback/page.tsx). Everything
// downstream (auth-context, the rest of the app) only ever sees this app's
// own JWT, minted by POST /api/auth/exchange -- see auth-context.tsx.
//
// Placeholder fallbacks (matching api.ts's NEXT_PUBLIC_API_URL pattern) so
// `next build`/CI doesn't require real Supabase credentials to succeed --
// createClient() throws immediately at module-eval time without a
// well-formed URL, which otherwise fails prerendering. Sign-in will fail at
// runtime without real env vars, but the build itself doesn't depend on them.
export const supabaseClient = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL ?? "https://placeholder.supabase.co",
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "placeholder-anon-key"
);
