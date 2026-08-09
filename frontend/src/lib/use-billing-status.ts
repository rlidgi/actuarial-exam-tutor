"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, type BillingStatus } from "./api";

export function useBillingStatus(token: string | null, examCode: string) {
  const [status, setStatus] = useState<BillingStatus | null>(null);
  // exam-context.tsx starts at a default exam code and swaps in the
  // localStorage-persisted one right after mount, firing a second request
  // before the first resolves. Without this guard, whichever response
  // resolves last wins the race and can overwrite the correct exam's
  // status with a stale one from the exam that was selected only briefly.
  const latestExamCodeRef = useRef(examCode);
  useEffect(() => {
    latestExamCodeRef.current = examCode;
  }, [examCode]);

  const refresh = useCallback(() => {
    if (!token) return;
    const requestedExamCode = examCode;
    api
      .getBillingStatus(token, examCode)
      .then((result) => {
        if (latestExamCodeRef.current === requestedExamCode) {
          setStatus(result);
        }
      })
      .catch(() => {});
  }, [token, examCode]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { status, refresh };
}
