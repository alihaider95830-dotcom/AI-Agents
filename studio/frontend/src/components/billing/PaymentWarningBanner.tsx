"use client";

import { useState } from "react";
import { AlertTriangle, Info, LoaderCircle } from "lucide-react";

import { useSupabaseAccessToken } from "@/hooks/useSupabaseAccessToken";
import {
  createBillingPortal,
  retryPayment,
} from "@/lib/api/billing";
import { ApiError } from "@/lib/api/client";

interface PaymentWarningBannerProps {
  subscriptionStatus: string | null;
}

export const PaymentWarningBanner = ({
  subscriptionStatus,
}: PaymentWarningBannerProps): JSX.Element | null => {
  const { token } = useSupabaseAccessToken();
  const [message, setMessage] = useState<string | null>(null);
  const [messageTone, setMessageTone] = useState<"success" | "error">("success");
  const [isRetrying, setIsRetrying] = useState(false);
  const [isOpeningPortal, setIsOpeningPortal] = useState(false);

  if (subscriptionStatus !== "past_due" && subscriptionStatus !== "paused") {
    return null;
  }

  const handleRetryPayment = async (): Promise<void> => {
    if (!token) {
      setMessageTone("error");
      setMessage("Your session is not ready yet.");
      return;
    }

    try {
      setIsRetrying(true);
      setMessage(null);
      await retryPayment(token);
      setMessageTone("success");
      setMessage("Payment retried — check back shortly.");
    } catch (error) {
      setMessageTone("error");
      if (error instanceof ApiError && error.status === 402) {
        setMessage(error.message);
      } else if (error instanceof Error) {
        setMessage(error.message);
      } else {
        setMessage("Payment retry failed.");
      }
    } finally {
      setIsRetrying(false);
    }
  };

  const handleOpenPortal = async (): Promise<void> => {
    if (!token) {
      setMessageTone("error");
      setMessage("Your session is not ready yet.");
      return;
    }

    try {
      setIsOpeningPortal(true);
      const response = await createBillingPortal(token);
      window.location.href = response.portal_url;
    } catch (error) {
      setMessageTone("error");
      setMessage(
        error instanceof Error
          ? error.message
          : "Unable to open billing portal.",
      );
      setIsOpeningPortal(false);
    }
  };

  const isPastDue = subscriptionStatus === "past_due";

  return (
    <section
      className={
        isPastDue
          ? "border-b border-rose-200 bg-rose-50 px-4 py-3 text-rose-900 dark:border-rose-900/50 dark:bg-rose-950/20 dark:text-rose-200"
          : "border-b border-zinc-200 bg-zinc-50 px-4 py-3 text-zinc-900 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-100"
      }
    >
      <div className="mx-auto flex max-w-6xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="flex items-center gap-2 text-sm font-semibold tracking-tight">
            {isPastDue ? (
              <AlertTriangle className="h-4 w-4 shrink-0 text-rose-500" aria-hidden="true" />
            ) : (
              <Info className="h-4 w-4 shrink-0 text-zinc-500" aria-hidden="true" />
            )}
            <span>
              {isPastDue
                ? "Payment failed. Update your payment method to keep your Pro access."
                : "Subscription paused. Reactivate to continue generating reports."}
            </span>
          </p>
          {message ? (
            <p
              className={
                messageTone === "success"
                  ? "mt-1 text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400"
                  : "mt-1 text-xs font-bold uppercase tracking-wider text-rose-600 dark:text-rose-400"
              }
            >
              {message}
            </p>
          ) : null}
        </div>

        <div className="flex flex-wrap gap-2">
          {isPastDue ? (
            <button
              className="inline-flex h-8 items-center justify-center gap-2 rounded-full bg-rose-600 px-4 text-xs font-bold uppercase tracking-wider text-white transition hover:bg-rose-700 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isRetrying}
              onClick={() => {
                void handleRetryPayment();
              }}
              type="button"
            >
              {isRetrying ? <LoaderCircle className="h-3 w-3 animate-spin" /> : null}
              Retry
            </button>
          ) : null}
          <button
            className="inline-flex h-8 items-center justify-center gap-2 rounded-full border border-current px-4 text-xs font-bold uppercase tracking-wider transition hover:bg-white/20 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isOpeningPortal}
            onClick={() => {
              void handleOpenPortal();
            }}
            type="button"
          >
            {isOpeningPortal ? <LoaderCircle className="h-3 w-3 animate-spin" /> : null}
            {isPastDue ? "Fix payment" : "Reactivate"}
          </button>
        </div>
      </div>
    </section>
  );
};
