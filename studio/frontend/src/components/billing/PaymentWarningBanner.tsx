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
          ? "border-b border-amber-200 bg-amber-50 px-4 py-3 text-amber-950 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100"
          : "border-b border-blue-200 bg-blue-50 px-4 py-3 text-blue-950 dark:border-blue-900 dark:bg-blue-950/40 dark:text-blue-100"
      }
    >
      <div className="mx-auto flex max-w-6xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="flex items-center gap-2 text-sm font-medium">
            {isPastDue ? (
              <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden="true" />
            ) : (
              <Info className="h-4 w-4 shrink-0" aria-hidden="true" />
            )}
            <span>
              {isPastDue
                ? "Your payment failed. Update your payment method to keep your Pro access."
                : "Your subscription is paused. Reactivate to generate new reports."}
            </span>
          </p>
          {message ? (
            <p
              className={
                messageTone === "success"
                  ? "mt-1 text-sm text-emerald-700 dark:text-emerald-200"
                  : "mt-1 text-sm text-red-700 dark:text-red-200"
              }
            >
              {message}
            </p>
          ) : null}
        </div>

        <div className="flex flex-wrap gap-2">
          {isPastDue ? (
            <button
              className="inline-flex h-9 items-center justify-center gap-2 rounded-lg bg-amber-600 px-3 text-sm font-medium text-white transition hover:bg-amber-700 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isRetrying}
              onClick={() => {
                void handleRetryPayment();
              }}
              type="button"
            >
              {isRetrying ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
              Retry payment
            </button>
          ) : null}
          <button
            className="inline-flex h-9 items-center justify-center gap-2 rounded-lg border border-current px-3 text-sm font-medium transition hover:bg-white/50 disabled:cursor-not-allowed disabled:opacity-60 dark:hover:bg-slate-950/40"
            disabled={isOpeningPortal}
            onClick={() => {
              void handleOpenPortal();
            }}
            type="button"
          >
            {isOpeningPortal ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
            {isPastDue ? "Update payment method" : "Reactivate subscription"}
          </button>
        </div>
      </div>
    </section>
  );
};
