import type { ReactNode } from "react";
import { AppShell } from "@/components/app-shell";
import { ChatViewProvider } from "@/lib/chat-view-context";
import { ExamProvider } from "@/lib/exam-context";

export default function AppGroupLayout({ children }: { children: ReactNode }) {
  return (
    <ExamProvider>
      <ChatViewProvider>
        <AppShell>{children}</AppShell>
      </ChatViewProvider>
    </ExamProvider>
  );
}
