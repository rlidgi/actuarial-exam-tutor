"use client";

import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

// Coordinates the sidebar (AppShell, which owns the date list and the "New
// Conversation" button) with the chat page (which owns what's actually
// displayed) without coupling them directly -- neither one needs to know
// the other's internals, just this shared bit of view state.
interface ChatViewState {
  // Which past day is being browsed, or null for the live view. Sidebar
  // sets this on a date click; the chat page reads it to decide what to
  // fetch/display, and clears it back to null itself when the student
  // sends a message while browsing a past day (auto-jump back to live).
  selectedDate: string | null;
  setSelectedDate: (date: string | null) => void;

  // Bumped by the sidebar's "New Conversation" button. The chat page
  // watches this in a useEffect to clear its displayed live messages --
  // a counter rather than a boolean so every click is a distinct signal
  // even if the value would otherwise be a no-op change.
  newConversationSignal: number;
  startNewConversation: () => void;

  // Bumped by the chat page after a message is successfully sent, so the
  // sidebar knows to refetch the day list (today's date may be new).
  historyDaysVersion: number;
  refreshHistoryDays: () => void;
}

const ChatViewContext = createContext<ChatViewState | null>(null);

export function ChatViewProvider({ children }: { children: ReactNode }) {
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [newConversationSignal, setNewConversationSignal] = useState(0);
  const [historyDaysVersion, setHistoryDaysVersion] = useState(0);

  const startNewConversation = useCallback(() => {
    setSelectedDate(null);
    setNewConversationSignal((n) => n + 1);
  }, []);

  const refreshHistoryDays = useCallback(() => {
    setHistoryDaysVersion((n) => n + 1);
  }, []);

  return (
    <ChatViewContext.Provider
      value={{
        selectedDate,
        setSelectedDate,
        newConversationSignal,
        startNewConversation,
        historyDaysVersion,
        refreshHistoryDays,
      }}
    >
      {children}
    </ChatViewContext.Provider>
  );
}

export function useChatView(): ChatViewState {
  const ctx = useContext(ChatViewContext);
  if (!ctx) {
    throw new Error("useChatView must be used within a ChatViewProvider");
  }
  return ctx;
}
