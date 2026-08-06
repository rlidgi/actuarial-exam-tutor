"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api";
import { MessageContent } from "@/components/message-content";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPage() {
  const { token, loading } = useAuth();
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!loading && !token) {
      router.push("/login");
    }
  }, [loading, token, router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!token || !input.trim() || sending) return;

    const text = input.trim();
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setSending(true);
    setError(null);

    try {
      const response = await api.sendMessage(token, text);
      setMessages((prev) => [...prev, { role: "assistant", content: response.reply }]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to reach the tutor. Try again.");
    } finally {
      setSending(false);
    }
  };

  if (loading || !token) {
    return null;
  }

  return (
    <div className="flex-1 flex flex-col max-w-2xl w-full mx-auto p-4">
      <div className="flex-1 overflow-y-auto flex flex-col gap-3 py-4">
        {messages.length === 0 && (
          <p className="text-sm text-black/50 dark:text-white/50">
            Ask a question about SOA Exam P, or say what you&apos;d like to study.
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`rounded-lg px-4 py-2 whitespace-pre-wrap text-sm max-w-[85%] ${
              m.role === "user"
                ? "self-end bg-foreground text-background"
                : "self-start bg-black/5 dark:bg-white/10"
            }`}
          >
            <MessageContent text={m.content} />
          </div>
        ))}
        {sending && (
          <div className="self-start rounded-lg px-4 py-2 text-sm bg-black/5 dark:bg-white/10 text-black/50 dark:text-white/50">
            Thinking...
          </div>
        )}
        {error && <p className="text-sm text-red-600">{error}</p>}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 pt-2 border-t border-black/10 dark:border-white/10">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={sending}
          className="flex-1 border border-black/20 dark:border-white/20 rounded px-3 py-2 bg-transparent"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="rounded bg-foreground text-background px-4 py-2 font-medium disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
