"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type BillingStatus } from "./api";

export function useBillingStatus(token: string | null) {
  const [status, setStatus] = useState<BillingStatus | null>(null);

  const refresh = useCallback(() => {
    if (!token) return;
    api.getBillingStatus(token).then(setStatus).catch(() => {});
  }, [token]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { status, refresh };
}
