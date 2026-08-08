import type { ReactNode } from "react";
import { AppShell } from "@/components/app-shell";
import { ChatViewProvider } from "@/lib/chat-view-context";

export default function AppGroupLayout({ children }: { children: ReactNode }) {
  return (
    <ChatViewProvider>
      <AppShell>{children}</AppShell>
    </ChatViewProvider>
  );
}
