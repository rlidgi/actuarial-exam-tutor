import Link from "next/link";
import { type BillingStatus } from "@/lib/api";

export function TrialBanner({
  status,
  examCode,
}: {
  status: BillingStatus | null;
  examCode: string;
}) {
  if (!status || status.subscribed) return null;

  const exhausted = status.free_turns_remaining <= 0;

  return (
    <div
      className={`chat-column mx-auto w-full px-1 pb-2 text-sm ${
        exhausted ? "text-redink" : "text-pencil"
      }`}
    >
      {exhausted ? (
        <span>Your free trial is used up. </span>
      ) : (
        <span>
          Free trial: {status.free_turns_remaining} of {status.free_trial_total} tutor messages
          left.{" "}
        </span>
      )}
      <Link href={`/subscribe?exam=${examCode}`} className="font-medium text-ledger underline">
        Subscribe to Exam {examCode}
      </Link>{" "}
      for unlimited access.
    </div>
  );
}
