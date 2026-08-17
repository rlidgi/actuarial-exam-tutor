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
import { FRESH_LOGIN_STORAGE_KEY, useAuth } from "@/lib/auth-context";
import { api, ApiError, isAuthError, type ChatMessageDTO } from "@/lib/api";
import { reportAdsConversion, SUBSCRIBE_CONVERSION_LABEL } from "@/lib/gtag";
import { useChatView } from "@/lib/chat-view-context";
import { useExam } from "@/lib/exam-context";
import { useBillingStatus } from "@/lib/use-billing-status";
import { MessageContent } from "@/components/message-content";
import { NotationPicker } from "@/components/notation-picker";
import { CameraCaptureModal } from "@/components/camera-capture-modal";
import { TrialBanner } from "@/components/trial-banner";
import { ChatSkeleton } from "@/components/skeleton";

interface DisplayMessage extends ChatMessageDTO {
  imagePreviewUrl?: string;
}

// "New Conversation" (and a fresh login) only clear liveMessages in memory
// -- there's nothing server-side marking a restart boundary, since /restart
// just appends one more message to the same day's history. Navigating away
// (a real route change, not just client-side view state) and back remounts
// this component fresh, losing that in-memory clear entirely: /open then
// returns the *whole* day's history again, same as browsing today's date
// in the sidebar. Persisting which message the last restart started from
// lets a remount re-apply the same cut client-side. Keyed by exam only (not
// date) since only today's restart is ever relevant -- yesterday's marker
// just won't match anything in today's fetched messages and is harmlessly
// overwritten by the next restart.
function restartMarkerKey(examCode: string): string {
  return `actuarial_tutor_restart_marker_${examCode}`;
}

function saveRestartMarker(examCode: string, content: string) {
  const today = new Date().toISOString().slice(0, 10); // UTC, matches the backend's "today"
  window.localStorage.setItem(restartMarkerKey(examCode), JSON.stringify({ date: today, content }));
}

// Cuts today's full message list down to just what's after the last
// restart, if one happened today -- falls back to the full list (no cut)
// whenever there's no marker, it's from a previous day, or the marked
// message isn't found (e.g. history pruning) so this never hides real
// messages by mistake.
function applyRestartMarker(examCode: string, messages: ChatMessageDTO[]): ChatMessageDTO[] {
  const raw = window.localStorage.getItem(restartMarkerKey(examCode));
  if (!raw) return messages;
  let marker: { date: string; content: string };
  try {
    marker = JSON.parse(raw);
  } catch {
    return messages;
  }
  const today = new Date().toISOString().slice(0, 10);
  if (marker.date !== today) return messages;
  const cutIndex = messages.findLastIndex((m) => m.role === "assistant" && m.content === marker.content);
  return cutIndex === -1 ? messages : messages.slice(cutIndex);
}

// Reads the ?checkout=success&session_id=... query set by Stripe Checkout's
// success_url, syncs the subscription once, then strips the params. Split
// out from ChatPage since useSearchParams requires a Suspense boundary.
function CheckoutSyncHandler({
  token,
  email,
  onSynced,
}: {
  token: string | null;
  email: string | null;
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
      .then((r) => {
        // Only a confirmed, successful sync is a real completed purchase --
        // firing on a failed/incomplete sync would report conversions for
        // checkouts that never actually went through.
        if (r.ok) reportAdsConversion(SUBSCRIBE_CONVERSION_LABEL, email ?? undefined);
      })
      .catch(() => {})
      .finally(() => {
        onSynced();
        // Clears the query params, which also removes them from
        // searchParams -- the guard above then short-circuits on the
        // resulting re-render instead of re-syncing.
        router.replace("/chat");
      });
  }, [token, email, searchParams, router, onSynced]);

  return null;
}

// Shown while waiting for the tutor's reply to start streaming in (see
// awaitingFirstToken) -- once real text starts arriving, the growing
// message bubble itself is the "it's working" signal, so this disappears.
function ThinkingIndicator() {
  return (
    <div className="self-start rounded bg-paper-raised px-3 py-2.5">
      <div className="thinking-dots" role="status" aria-label="Tutor is thinking">
        <span />
        <span />
        <span />
      </div>
    </div>
  );
}

export default function ChatPage() {
  const { token, loading, redirectToExpiredLogin } = useRequireAuth();
  const { email } = useAuth();
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
  // True from when a turn starts until the first streamed chunk of the
  // tutor's reply arrives -- distinct from `sending` (which stays true for
  // the whole turn) so the "thinking" indicator hides once real text
  // starts appearing instead of showing alongside the growing reply.
  const [awaitingFirstToken, setAwaitingFirstToken] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [blocked, setBlocked] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const viewingPastDay = selectedDate !== null;
  const messages = viewingPastDay ? dayMessages : liveMessages;
  const dayLoading = viewingPastDay && selectedDate !== loadedDate;

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

  // Populates the live view: on mount, on an exam switch, and whenever the
  // student returns to live from browsing a past day, this restores
  // today's actual conversation (including generating the tutor's opening
  // message server-side, if nothing's been sent yet today -- see
  // POST /api/chat/open). "New Conversation" reuses the same effect rather
  // than a separate one specifically to avoid two fetches racing when it's
  // clicked while browsing a past day (which flips viewingPastDay AND bumps
  // newConversationSignal in the same render) -- a ref (not state) tracks
  // the last-handled signal so updating it doesn't itself retrigger this
  // effect the way updating state would.
  // examCode is tracked alongside the signal (not just the signal alone)
  // because app-shell.tsx's exam switcher also bumps newConversationSignal
  // when it changes examCode -- without this, switching exams would hit
  // /restart (mid-conversation framing) instead of /open (a proper first
  // load) for the newly selected exam.
  // A fresh sign-in gets the same /restart treatment as clicking "New
  // Conversation" -- see FRESH_LOGIN_STORAGE_KEY in auth-context.tsx, set
  // only by a real completeSupabaseSignIn, never by a page refresh that
  // just restores an existing token. Consumed (read then cleared) here so
  // it only fires once per login, not on every subsequent mount.
  const handledRef = useRef({ signal: newConversationSignal, examCode });
  useEffect(() => {
    if (!token || viewingPastDay) return;
    const freshLogin = window.sessionStorage.getItem(FRESH_LOGIN_STORAGE_KEY) === "1";
    if (freshLogin) window.sessionStorage.removeItem(FRESH_LOGIN_STORAGE_KEY);
    const isRestart =
      freshLogin ||
      (newConversationSignal !== handledRef.current.signal && examCode === handledRef.current.examCode);
    handledRef.current = { signal: newConversationSignal, examCode };

    let cancelled = false;
    if (isRestart) setLiveMessages([]);
    // Deliberately synchronous, ahead of the async call below -- these
    // drive the thinking indicator and clear any stale error right when
    // the fetch starts, not after some other trigger. /open and /restart
    // aren't streamed (unlike a real reply, there's no "first chunk" to
    // distinguish), so awaitingFirstToken just stays true for the whole
    // fetch -- the indicator shows the entire time, same as the loading
    // phase of a real streamed turn.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSending(true);
    setAwaitingFirstToken(true);
    setError(null);

    const load = isRestart
      ? api.restartChat(token, examCode).then((r) => {
          if (r.blocked) {
            if (!cancelled) setBlocked(true);
            return null;
          }
          if (r.message) saveRestartMarker(examCode, r.message.content);
          return r.message ? [r.message] : [];
        })
      : api.openChat(token, examCode).then((r) => applyRestartMarker(examCode, r.messages));

    load
      .then((msgs) => {
        if (!cancelled && msgs) setLiveMessages(msgs);
      })
      .catch((err) => {
        if (cancelled) return;
        if (isAuthError(err)) {
          redirectToExpiredLogin();
          return;
        }
        setError(err instanceof ApiError ? err.message : "Failed to reach the tutor. Try again.");
      })
      .finally(() => {
        if (!cancelled) {
          setSending(false);
          setAwaitingFirstToken(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [token, examCode, viewingPastDay, newConversationSignal, redirectToExpiredLogin]);

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
    setAwaitingFirstToken(true);
    setError(null);
    setBlocked(false);

    try {
      // A plain `let` read inside the setLiveMessages updater below would be
      // a stale-closure bug here: React doesn't call these updaters
      // synchronously as each delta arrives (several can queue before any of
      // them actually run), so by the time the *first* delta's updater runs,
      // a shared mutable flag would already reflect a *later* delta's value.
      // Snapshotting into a fresh `const` per iteration closes over the
      // value as of that delta, immune to when React actually applies it.
      let streaming = false;
      for await (const event of api.sendMessage(token, examCode, text, imageToSend)) {
        if (event.blocked) {
          // No reply to show -- roll back the optimistic user bubble so the
          // transcript doesn't end on an unanswered question.
          setLiveMessages((prev) => prev.slice(0, -1));
          setBlocked(true);
          refreshBilling();
          return;
        }
        if (event.delta !== undefined) {
          const delta = event.delta;
          const isFirstChunk = !streaming;
          setAwaitingFirstToken(false);
          setLiveMessages((prev) =>
            isFirstChunk
              ? [...prev, { role: "assistant", content: delta }]
              : [
                  ...prev.slice(0, -1),
                  { ...prev[prev.length - 1], content: prev[prev.length - 1].content + delta },
                ]
          );
          streaming = true;
        }
        if (event.done) {
          refreshHistoryDays();
        }
      }
    } catch (err) {
      if (isAuthError(err)) {
        redirectToExpiredLogin();
        return;
      }
      setError(err instanceof ApiError ? err.message : "Failed to reach the tutor. Try again.");
    } finally {
      setSending(false);
      setAwaitingFirstToken(false);
      // The textarea is `disabled` while sending, which the browser force-
      // blurs -- refocus once React re-enables it (after this render
      // commits, hence requestAnimationFrame) so the student can keep
      // typing the next question without reaching for the mouse.
      requestAnimationFrame(() => textareaRef.current?.focus());
    }
  };

  const runRegenerate = async (editedMessage?: string) => {
    if (!token || sending || liveMessages.length === 0) return;
    setSending(true);
    setAwaitingFirstToken(true);
    setError(null);
    setBlocked(false);
    const questionText = editedMessage ?? liveMessages[liveMessages.length - 2]?.content ?? "";
    try {
      let streaming = false;
      for await (const event of api.regenerate(token, examCode, editedMessage)) {
        if (event.blocked) {
          // The backend checks access before deleting anything, so the
          // existing exchange is untouched -- nothing to roll back here.
          setBlocked(true);
          refreshBilling();
          return;
        }
        if (event.delta !== undefined) {
          const delta = event.delta;
          const isFirstChunk = !streaming;
          setAwaitingFirstToken(false);
          setLiveMessages((prev) =>
            isFirstChunk
              ? [
                  ...prev.slice(0, -2),
                  { role: "user", content: questionText },
                  { role: "assistant", content: delta },
                ]
              : [
                  ...prev.slice(0, -1),
                  { role: "assistant", content: prev[prev.length - 1].content + delta },
                ]
          );
          streaming = true;
        }
        if (event.done) {
          refreshHistoryDays();
        }
      }
    } catch (err) {
      if (isAuthError(err)) {
        redirectToExpiredLogin();
        return;
      }
      setError(err instanceof ApiError ? err.message : "Failed to regenerate. Try again.");
    } finally {
      setSending(false);
      setAwaitingFirstToken(false);
    }
  };

  const handleEdit = () => {
    const lastUserMessage = [...liveMessages].reverse().find((m) => m.role === "user");
    const edited = window.prompt("Edit your question:", lastUserMessage?.content ?? "");
    if (edited === null || !edited.trim()) return;
    runRegenerate(edited.trim());
  };

  if (loading || !token) {
    return <ChatSkeleton />;
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <Suspense fallback={null}>
        <CheckoutSyncHandler token={token} email={email} onSynced={refreshBilling} />
      </Suspense>
      <div className="flex flex-1 flex-col overflow-y-auto px-4 py-4 md:px-6">
        <TrialBanner status={billingStatus} examCode={examCode} />
        <div className="chat-column mx-auto flex w-full flex-1 flex-col gap-3">
          {viewingPastDay && messages.length === 0 && !dayLoading && (
            <p className="text-sm text-pencil">No messages on this day.</p>
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
            // The tutor's proactive opening message (see POST /api/chat/open
            // and /restart) can be the only message present, with no
            // preceding user question -- there's nothing for the backend to
            // regenerate in that case (_delete_last_exchange needs a prior
            // user message), so require one exists before offering the button.
            const showRegenerate =
              !viewingPastDay && isLastAssistant && messages.some((n) => n.role === "user");
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

          {sending && awaitingFirstToken && <ThinkingIndicator />}
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
        <div className="chat-column mx-auto flex w-full flex-col gap-2">
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
