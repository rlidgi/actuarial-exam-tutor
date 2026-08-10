"use client";

import {
  Suspense,
  useEffect,
  useRef,
  useState,
  type ClipboardEvent,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError, isAuthError, type ChatMessageDTO } from "@/lib/api";
import { useChatView } from "@/lib/chat-view-context";
import { useExam } from "@/lib/exam-context";
import { useBillingStatus } from "@/lib/use-billing-status";
import { MessageContent } from "@/components/message-content";
import { NotationPicker } from "@/components/notation-picker";
import { CameraCaptureModal } from "@/components/camera-capture-modal";
import { TrialBanner } from "@/components/trial-banner";

interface DisplayMessage extends ChatMessageDTO {
  imagePreviewUrl?: string;
}

// Reads the ?checkout=success&session_id=... query set by Stripe Checkout's
// success_url, syncs the subscription once, then strips the params. Split
// out from ChatPage since useSearchParams requires a Suspense boundary.
function CheckoutSyncHandler({
  token,
  onSynced,
}: {
  token: string | null;
  onSynced: () => void;
}) {
  const searchParams = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    if (!token) return;
    const sessionId = searchParams.get("session_id");
    if (searchParams.get("checkout") !== "success" || !sessionId) return;

    api
      .syncCheckoutSession(token, sessionId)
      .catch(() => {})
      .finally(() => {
        onSynced();
        // Clears the query params, which also removes them from
        // searchParams -- the guard above then short-circuits on the
        // resulting re-render instead of re-syncing.
        router.replace("/chat");
      });
  }, [token, searchParams, router, onSynced]);

  return null;
}

export default function ChatPage() {
  const { token, loading, redirectToExpiredLogin } = useRequireAuth();
  const { selectedDate, setSelectedDate, newConversationSignal, refreshHistoryDays } =
    useChatView();
  const { examCode } = useExam();
  const { status: billingStatus, refresh: refreshBilling } = useBillingStatus(token, examCode);

  const [liveMessages, setLiveMessages] = useState<DisplayMessage[]>([]);
  const [dayMessages, setDayMessages] = useState<DisplayMessage[]>([]);
  const [loadedDate, setLoadedDate] = useState<string | null>(null);

  const [input, setInput] = useState("");
  const [attachedImage, setAttachedImage] = useState<File | null>(null);
  const [attachedPreviewUrl, setAttachedPreviewUrl] = useState<string | null>(null);
  const [cameraOpen, setCameraOpen] = useState(false);

  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [blocked, setBlocked] = useState(false);

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
      .getHistoryDay(token, examCode, selectedDate)
      .then((r) => {
        setDayMessages(r.messages);
        setLoadedDate(selectedDate);
      })
      .catch(() => setError("Couldn't load that day's conversation."));
  }, [token, examCode, selectedDate]);

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

  // Mirrors the server's authoritative gate purely for a snappy UI/one
  // fewer round-trip -- the server enforces the real limit independently
  // (see the {blocked: "trial_exhausted"} handling below) regardless of
  // what this says, so a stale client-side status here is never unsafe,
  // just occasionally lets one extra request through to the real check.
  const hasChatAccess =
    !billingStatus || billingStatus.subscribed || billingStatus.free_turns_remaining > 0;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!token || sending) return;
    const text = input.trim();
    if (!text && !attachedImage) return;
    if (!hasChatAccess) {
      setBlocked(true);
      return;
    }

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
    // autoGrow reads scrollHeight off the DOM directly, so it must run after
    // React commits the cleared value -- otherwise it measures the textarea
    // still showing the old multi-line content and the grown height never
    // shrinks back down (same ordering issue insertSnippet already guards
    // against above).
    requestAnimationFrame(() => autoGrow());
    clearAttachedImage({ revoke: false });
    setSending(true);
    setError(null);
    setBlocked(false);

    try {
      const response = await api.sendMessage(token, examCode, text, imageToSend);
      if (response.blocked) {
        // No reply to show -- roll back the optimistic user bubble so the
        // transcript doesn't end on an unanswered question.
        setLiveMessages((prev) => prev.slice(0, -1));
        setBlocked(true);
        refreshBilling();
        return;
      }
      setLiveMessages((prev) => [...prev, { role: "assistant", content: response.reply ?? "" }]);
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
    setBlocked(false);
    try {
      const response = await api.regenerate(token, examCode, editedMessage);
      if (response.blocked) {
        // The backend checks access before deleting anything, so the
        // existing exchange is untouched -- nothing to roll back here.
        setBlocked(true);
        refreshBilling();
        return;
      }
      const questionText = editedMessage ?? liveMessages[liveMessages.length - 2]?.content ?? "";
      setLiveMessages((prev) => [
        ...prev.slice(0, -2),
        { role: "user", content: questionText },
        { role: "assistant", content: response.reply ?? "" },
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
      <Suspense fallback={null}>
        <CheckoutSyncHandler token={token} onSynced={refreshBilling} />
      </Suspense>
      <div className="flex flex-1 flex-col overflow-y-auto px-4 py-4 md:px-6">
        <TrialBanner status={billingStatus} examCode={examCode} />
        <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-3">
          {messages.length === 0 && !dayLoading && (
            <p className="text-sm text-pencil">
              {viewingPastDay
                ? "No messages on this day."
                : `Ask a question about Exam ${examCode}, paste or upload a screenshot of a problem, or say what you'd like to work on.`}
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
          {blocked && (
            <div className="self-start rounded border border-redink/30 bg-redink/5 px-3 py-2 text-sm text-redink">
              You&apos;ve used up your free trial messages.{" "}
              <Link
                href={`/subscribe?exam=${examCode}`}
                className="font-medium underline"
              >
                Subscribe
              </Link>{" "}
              for unlimited access.
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
              className="flex flex-shrink-0 items-center gap-1 rounded-md border border-rule bg-paper-raised px-2 py-1.5 text-xs text-pencil hover:border-ledger-bright hover:text-ledger-bright"
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
