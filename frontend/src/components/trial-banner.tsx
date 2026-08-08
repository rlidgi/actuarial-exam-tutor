import Link from "next/link";
import { EXAM_CODE, type BillingStatus } from "@/lib/api";

export function TrialBanner({ status }: { status: BillingStatus | null }) {
  if (!status || status.subscribed) return null;

  const exhausted = status.free_turns_remaining <= 0;

  return (
    <div
      className={`mx-auto w-full max-w-3xl px-1 pb-2 text-sm ${
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
      <Link href={`/subscribe?exam=${EXAM_CODE}`} className="font-medium text-ledger underline">
        Subscribe to Exam P
      </Link>{" "}
      for unlimited access.
    </div>
  );
}
