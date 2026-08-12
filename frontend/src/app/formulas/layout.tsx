import type { ReactNode } from "react";
import { ExamProvider } from "@/lib/exam-context";

export default function FormulasLayout({ children }: { children: ReactNode }) {
  return <ExamProvider>{children}</ExamProvider>;
}
