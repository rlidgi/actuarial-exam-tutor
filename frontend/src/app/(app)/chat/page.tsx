"use client";

import {
  useEffect,
  useRef,
  useState,
  type ClipboardEvent,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError, isAuthError, type ChatMessageDTO } from "@/lib/api";
import { useChatView } from "@/lib/chat-view-context";
import { MessageContent } from "@/components/message-content";
import { NotationPicker } from "@/components/notation-picker";
import { CameraCaptureModal } from "@/components/camera-capture-modal";

interface DisplayMessage extends ChatMessageDTO {
  imagePreviewUrl?: string;
}

export default function ChatPage() {
  const { token, loading, redirectToExpiredLogin } = useRequireAuth();
  const { selectedDate, setSelectedDate, newConversationSignal, refreshHistoryDays } =
    useChatView();

  const [liveMessages, setLiveMessages] = useState<DisplayMessage[]>([]);
  const [dayMessages, setDayMessages] = useState<DisplayMessage[]>([]);
  const [loadedDate, setLoadedDate] = useState<string | null>(null);

  const [input, setInput] = useState("");
  const [attachedImage, setAttachedImage] = useState<File | null>(null);
  const [attachedPreviewUrl, setAttachedPreviewUrl] = useState<string | null>(null);
  const [cameraOpen, setCameraOpen] = useState(false);

  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const viewingPastDay = selectedDate !== null;
  const messages = viewingPastDay ? dayMessages : liveMessages;
  const dayLoading = viewingPastDay && selectedDate !== loadedDate;

  // "New Conversation" never resets any backend memory -- it's the same
  // ongoing session either way -- it just clears what's displayed, the
  // same as a page reload already does today. Adjusting state during
  // render (rather than in an effect) on a signal change, per React's own
  // guidance for this pattern -- avoids an extra render pass.
  const [handledSignal, setHandledSignal] = useState(newConversationSignal);
  if (newConversationSignal !== handledSignal) {
    setHandledSignal(newConversationSignal);
    setLiveMessages([]);
  }

  useEffect(() => {
    if (!token || !selectedDate) return;
    api
      .getHistoryDay(token, selectedDate)
      .then((r) => {
        setDayMessages(r.messages);
        setLoadedDate(selectedDate);
      })
      .catch(() => setError("Couldn't load that day's conversation."));
  }, [token, selectedDate]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  // Only revokes the blob URL when the attachment is actually being
  // discarded (the composer's remove button). On send, the same URL is
  // handed off to the just-sent message bubble for its own display, so
  // revoking it here would break that bubble's image the moment the
  // composer clears -- see handleSubmit.
  const clearAttachedImage = ({ revoke = true }: { revoke?: boolean } = {}) => {
    if (revoke && attachedPreviewUrl) URL.revokeObjectURL(attachedPreviewUrl);
    setAttachedImage(null);
    setAttachedPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const attachImage = (file: File) => {
    if (attachedPreviewUrl) URL.revokeObjectURL(attachedPreviewUrl);
    setAttachedImage(file);
    setAttachedPreviewUrl(URL.createObjectURL(file));
  };

  const autoGrow = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  };

  const insertSnippet = (snippet: string) => {
    const el = textareaRef.current;
    if (!el) {
      setInput((prev) => prev + snippet);
      return;
    }
    const start = el.selectionStart ?? input.length;
    const end = el.selectionEnd ?? input.length;
    const next = input.slice(0, start) + snippet + input.slice(end);
    setInput(next);
    requestAnimationFrame(() => {
      el.focus();
      const cursor = start + snippet.length;
      el.setSelectionRange(cursor, cursor);
      autoGrow();
    });
  };

  const handlePaste = (e: ClipboardEvent<HTMLTextAreaElement>) => {
    for (const item of e.clipboardData.items) {
      if (item.type.startsWith("image/")) {
        const file = item.getAsFile();
        if (file) {
          attachImage(file);
          e.preventDefault();
        }
        return;
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      e.currentTarget.form?.requestSubmit();
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!token || sending) return;
    const text = input.trim();
    if (!text && !attachedImage) return;

    const imageToSend = attachedImage ?? undefined;
    const previewUrl = attachedPreviewUrl ?? undefined;

    // Sending while browsing a past day auto-jumps back to the live view --
    // there's only one active memory context, so there's no "sending into"
    // an old day.
    setSelectedDate(null);
    setLiveMessages((prev) => [
      ...prev,
      { role: "user", content: text, imagePreviewUrl: previewUrl },
    ]);
    setInput("");
    clearAttachedImage({ revoke: false });
    setSending(true);
    setError(null);

    try {
      const response = await api.sendMessage(token, text, imageToSend);
      setLiveMessages((prev) => [...prev, { role: "assistant", content: response.reply }]);
      refreshHistoryDays();
    } catch (err) {
      if (isAuthError(err)) {
        redirectToExpiredLogin();
        return;
      }
      setError(err instanceof ApiError ? err.message : "Failed to reach the tutor. Try again.");
    } finally {
      setSending(false);
    }
  };

  const runRegenerate = async (editedMessage?: string) => {
    if (!token || sending || liveMessages.length === 0) return;
    setSending(true);
    setError(null);
    try {
      const response = await api.regenerate(token, editedMessage);
      const questionText = editedMessage ?? liveMessages[liveMessages.length - 2]?.content ?? "";
      setLiveMessages((prev) => [
        ...prev.slice(0, -2),
        { role: "user", content: questionText },
        { role: "assistant", content: response.reply },
      ]);
      refreshHistoryDays();
    } catch (err) {
      if (isAuthError(err)) {
        redirectToExpiredLogin();
        return;
      }
      setError(err instanceof ApiError ? err.message : "Failed to regenerate. Try again.");
    } finally {
      setSending(false);
    }
  };

  const handleEdit = () => {
    const lastUserMessage = [...liveMessages].reverse().find((m) => m.role === "user");
    const edited = window.prompt("Edit your question:", lastUserMessage?.content ?? "");
    if (edited === null || !edited.trim()) return;
    runRegenerate(edited.trim());
  };

  if (loading || !token) {
    return null;
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex flex-1 flex-col overflow-y-auto px-4 py-4 md:px-6">
        <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-3">
          {messages.length === 0 && !dayLoading && (
            <p className="text-sm text-pencil">
              {viewingPastDay
                ? "No messages on this day."
                : "Ask a question about Exam P, paste or upload a screenshot of a problem, or say what you'd like to work on."}
            </p>
          )}
          {dayLoading && <p className="text-sm text-pencil">Loading...</p>}

          {messages.map((m, i) => {
            // Edit/regenerate belong to the last *exchange*, not the last
            // array item -- the user bubble of that exchange sits one
            // position before its assistant reply, so "last user message"
            // and "last assistant message" are tracked separately rather
            // than both being compared against messages.length - 1.
            const isLastUser = m.role === "user" && !messages.slice(i + 1).some((n) => n.role === "user");
            const isLastAssistant =
              m.role === "assistant" && i === messages.length - 1;
            const showEdit = !viewingPastDay && isLastUser;
            const showRegenerate = !viewingPastDay && isLastAssistant;
            return (
              <div
                key={i}
                className={`group max-w-[85%] rounded px-3 py-2 text-sm shadow-sm ${
                  m.role === "user"
                    ? "self-end border-r-2 border-pencil-soft bg-paper-raised"
                    : "self-start border-l-2 border-ledger bg-paper-raised"
                }`}
              >
                {m.imagePreviewUrl && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={m.imagePreviewUrl}
                    alt="Attached problem"
                    className="mb-2 max-h-40 rounded border border-rule"
                  />
                )}
                <MessageContent text={m.content} />
                {(showEdit || showRegenerate) && (
                  <div className="mt-2 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                    {showEdit && (
                      <button
                        type="button"
                        title="Edit and resend"
                        onClick={handleEdit}
                        className="rounded border border-rule bg-paper px-1.5 py-0.5 text-xs text-pencil hover:border-ledger-bright hover:text-ledger-bright"
                      >
                        &#9998;
                      </button>
                    )}
                    {showRegenerate && (
                      <button
                        type="button"
                        title="Regenerate"
                        onClick={() => runRegenerate(undefined)}
                        className="rounded border border-rule bg-paper px-1.5 py-0.5 text-xs text-pencil hover:border-ledger-bright hover:text-ledger-bright"
                      >
                        &#8635;
                      </button>
                    )}
                  </div>
                )}
              </div>
            );
          })}

          {sending && (
            <div className="self-start rounded bg-paper-raised px-3 py-2 text-sm text-pencil">
              Thinking...
            </div>
          )}
          {error && <p className="text-sm text-redink">{error}</p>}
          <div ref={bottomRef} />
        </div>
      </div>

      <form
        onSubmit={handleSubmit}
        className="border-t border-rule bg-paper px-4 py-3 md:px-6"
      >
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-2">
          {attachedPreviewUrl && (
            <div className="flex items-center gap-2">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={attachedPreviewUrl}
                alt="Attachment preview"
                className="max-h-16 rounded border border-rule"
              />
              <button
                type="button"
                onClick={() => clearAttachedImage()}
                title="Remove attached image"
                className="flex h-6 w-6 items-center justify-center rounded-full border border-rule bg-paper-raised text-pencil hover:border-redink hover:text-redink"
              >
                &times;
              </button>
            </div>
          )}

          {input.includes("$") && (
            <div className="rounded-md border border-rule bg-paper-raised px-3 py-1.5 text-sm text-ink">
              <MessageContent text={input} />
            </div>
          )}

          <div className="flex items-center gap-2">
            <label
              title="Attach a screenshot of a problem, or paste directly in the text box"
              className="flex h-9 w-9 flex-shrink-0 cursor-pointer items-center justify-center rounded-md border border-rule bg-paper-raised text-pencil hover:border-ledger-bright hover:text-ledger-bright"
            >
              &#128206;
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) attachImage(file);
                }}
              />
            </label>
            <button
              type="button"
              onClick={() => setCameraOpen(true)}
              title="Take a photo of your work"
              className="hidden flex-shrink-0 items-center gap-1 rounded-md border border-rule bg-paper-raised px-2 py-1.5 text-xs text-pencil hover:border-ledger-bright hover:text-ledger-bright sm:flex"
            >
              &#128247; Photo
            </button>
            <NotationPicker onInsert={insertSnippet} />
          </div>

          <div className="flex items-end gap-2">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                autoGrow();
              }}
              onPaste={handlePaste}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question or paste a problem..."
              disabled={sending}
              rows={1}
              className="max-h-40 flex-1 resize-none rounded border border-rule bg-transparent px-3 py-2 text-sm"
            />
            <button
              type="submit"
              disabled={sending || (!input.trim() && !attachedImage)}
              className="rounded-md bg-ledger px-4 py-2 text-sm font-semibold text-paper hover:bg-ledger-bright disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </div>
      </form>

      {cameraOpen && (
        <CameraCaptureModal
          onCapture={(file) => {
            attachImage(file);
            setCameraOpen(false);
          }}
          onClose={() => setCameraOpen(false)}
        />
      )}
    </div>
  );
}
