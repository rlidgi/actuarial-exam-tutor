import { createClient } from "@supabase/supabase-js";

// The ONLY place in the frontend that talks to Supabase directly -- Google
// OAuth and magic-link sign-in both go through this client (see
// components/sign-in-modal.tsx and app/auth/callback/page.tsx). Everything
// downstream (auth-context, the rest of the app) only ever sees this app's
// own JWT, minted by POST /api/auth/exchange -- see auth-context.tsx.
export const supabaseClient = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);
