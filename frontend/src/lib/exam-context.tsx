"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api, DEFAULT_EXAM_CODE, type ExamInfo } from "./api";
import { useAuth } from "./auth-context";

const EXAM_STORAGE_KEY = "actuarial_tutor_exam";

interface ExamState {
  examCode: string;
  // False for the one tick between mount and the localStorage read below --
  // examCode is only a guessed default (DEFAULT_EXAM_CODE) until this flips
  // true. Consumers that fetch exam-specific content on mount (manual/
  // formulas pages) key their fetch effect off this, not just examCode, so
  // they never fire a request for the wrong exam and then have to discard
  // it -- see manual/page.tsx and formulas/page.tsx.
  ready: boolean;
  exams: ExamInfo[];
  loading: boolean;
  setExamCode: (code: string) => Promise<void>;
}

const ExamContext = createContext<ExamState | null>(null);

export function ExamProvider({ children }: { children: ReactNode }) {
  const { token } = useAuth();
  const [examCode, setExamCodeState] = useState(DEFAULT_EXAM_CODE);
  const [ready, setReady] = useState(false);
  const [exams, setExams] = useState<ExamInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // One-time synchronous read, deliberately in an effect so it never runs
    // during SSR -- same pattern as auth-context.tsx's token read.
    const stored = window.localStorage.getItem(EXAM_STORAGE_KEY);
    if (stored) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setExamCodeState(stored);
    }
    setReady(true);
  }, []);

  useEffect(() => {
    api
      .getExams()
      .then((r) => setExams(r.exams))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  // Stable identity: consumers put this in effect dependency arrays.
  const setExamCode = useCallback(
    async (code: string) => {
      if (token) {
        // The user may not have a StudentProfile for a freshly-selected
        // exam yet -- mirrors the one-time ensureProfile call at signup,
        // just repeated per exam. Idempotent server-side (find-or-create).
        await api.ensureProfile(token, code);
      }
      window.localStorage.setItem(EXAM_STORAGE_KEY, code);
      setExamCodeState(code);
    },
    [token]
  );

  return (
    <ExamContext.Provider value={{ examCode, ready, exams, loading, setExamCode }}>
      {children}
    </ExamContext.Provider>
  );
}

export function useExam(): ExamState {
  const ctx = useContext(ExamContext);
  if (!ctx) {
    throw new Error("useExam must be used within an ExamProvider");
  }
  return ctx;
}
