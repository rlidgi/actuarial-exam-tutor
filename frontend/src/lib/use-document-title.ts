"use client";

import { useEffect } from "react";

// Next.js's Metadata API only works in Server Components, but every page
// under (app) and (public)/login,register is "use client" (they need
// hooks like useAuth/useRequireAuth) -- so without this, all of them fall
// back to the root layout's default title, indistinguishable from the
// landing page and from each other in anything that groups by page title
// (browser tabs, GA's "Page title" dimension, etc). Same suffix as the
// root layout's own title.template, so client-titled pages read
// identically to server-titled ones (Pricing, About, Contact).
export function useDocumentTitle(title: string) {
  useEffect(() => {
    document.title = `${title} -- Actuarial Exams Tutor`;
  }, [title]);
}
