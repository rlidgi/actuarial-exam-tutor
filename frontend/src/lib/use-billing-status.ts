"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type BillingStatus } from "./api";

export function useBillingStatus(token: string | null, examCode: string) {
  const [status, setStatus] = useState<BillingStatus | null>(null);

  const refresh = useCallback(() => {
    if (!token) return;
    api.getBillingStatus(token, examCode).then(setStatus).catch(() => {});
  }, [token, examCode]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { status, refresh };
}
