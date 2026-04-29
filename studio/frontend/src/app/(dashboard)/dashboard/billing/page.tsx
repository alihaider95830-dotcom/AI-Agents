"use client";

import { useEffect, useState } from "react";
import {
  CreditCard,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ExternalLink,
  ArrowUpCircle,
} from "lucide-react";
import { toast } from "sonner";

import { useAuthStore } from "@/store/authStore";
import {
  getUsageSummary,
  getPaymentStatus,
  getSubscription,
  createBillingPortal,
  createCheckoutSession,
  type UsageSummary,
  type PaymentStatus,
  type SubscriptionDetail,
} from "@/lib/api/billing";
import { env } from "@/lib/env";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function tierLabel(tier: string): string {
  return tier.charAt(0).toUpperCase() + tier.slice(1);
}

function formatDate(epoch: number | null | undefined): string {
  if (!epoch) return "—";
  return new Date(epoch * 1000).toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function statusBadge(status: string | null | undefined) {
  const s = status ?? "none";
  const map: Record<string, { label: string; cls: string }> = {
    active: {
      label: "Active",
      cls: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
    },
    trialing: {
      label: "Trial",
      cls: "bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-400",
    },
    past_due: {
      label: "Past Due",
      cls: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
    },
    canceled: {
      label: "Cancelled",
      cls: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
    },
    paused: {
      label: "Paused",
      cls: "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400",
    },
    none: {
      label: "Free Plan",
      cls: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
    },
  };
  const { label, cls } = map[s] ?? map["none"];
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${cls}`}>
      {label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ManagePortalButton({ token }: { token: string }) {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    try {
      const { portal_url } = await createBillingPortal(token);
      window.location.href = portal_url;
    } catch {
      toast.error("Could not open the billing portal. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      className="inline-flex items-center gap-2 rounded-lg bg-brand-ocean px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-ink disabled:opacity-60 dark:bg-brand-gold dark:text-slate-900 dark:hover:bg-amber-400"
      disabled={loading}
      id="manage-portal-btn"
      onClick={handleClick}
      type="button"
    >
      {loading ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <ExternalLink className="h-4 w-4" />
      )}
      Manage in Stripe Portal
    </button>
  );
}

function UpgradePlanButton({ token }: { token: string }) {
  const [loading, setLoading] = useState(false);

  const priceId = process.env.NEXT_PUBLIC_STRIPE_PRO_PRICE_ID ?? "";

  const handleClick = async () => {
    if (!priceId) {
      toast.error("No upgrade plan configured.");
      return;
    }
    setLoading(true);
    try {
      const origin = window.location.origin;
      const { checkout_url } = await createCheckoutSession(
        token,
        priceId,
        `${origin}/billing/success`,
        `${origin}/billing/cancelled`,
      );
      window.location.href = checkout_url;
    } catch {
      toast.error("Could not start checkout. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      className="inline-flex items-center gap-2 rounded-lg border border-brand-ocean px-4 py-2 text-sm font-semibold text-brand-ocean transition hover:bg-brand-ocean hover:text-white disabled:opacity-60 dark:border-brand-gold dark:text-brand-gold dark:hover:bg-brand-gold dark:hover:text-slate-900"
      disabled={loading}
      id="upgrade-plan-btn"
      onClick={handleClick}
      type="button"
    >
      {loading ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <ArrowUpCircle className="h-4 w-4" />
      )}
      Upgrade Plan
    </button>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function BillingPage(): JSX.Element {
  const token = useAuthStore((s) => s.token);
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [payment, setPayment] = useState<PaymentStatus | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionDetail | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;

    const load = async () => {
      try {
        const [u, p, s] = await Promise.all([
          getUsageSummary(token),
          getPaymentStatus(token),
          getSubscription(token),
        ]);
        setUsage(u);
        setPayment(p);
        setSubscription(s);
      } catch {
        setError("Unable to load billing information.");
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, [token]);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-brand-ocean dark:text-brand-gold" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3 text-center">
        <AlertCircle className="h-10 w-10 text-red-500" />
        <p className="text-slate-700 dark:text-slate-300">{error}</p>
      </div>
    );
  }

  const isFree = subscription?.status === "none";

  return (
    <div className="mx-auto max-w-3xl space-y-6 py-4">
      {/* Header */}
      <div>
        <h1 className="font-[var(--font-heading)] text-2xl font-semibold text-slate-900 dark:text-white">
          Billing &amp; Subscription
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Manage your plan, credits, and payment method.
        </p>
      </div>

      {/* Plan overview */}
      <div className="rounded-2xl border border-slate-200/70 bg-white/90 p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950/80">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-ocean/10 dark:bg-brand-gold/10">
              <CreditCard className="h-5 w-5 text-brand-ocean dark:text-brand-gold" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400">
                Current plan
              </p>
              <p className="font-[var(--font-heading)] text-xl font-semibold text-slate-900 dark:text-white">
                {usage ? tierLabel(usage.tier) : "—"}
              </p>
            </div>
          </div>
          {statusBadge(payment?.subscription_status)}
        </div>

        {/* Credits */}
        {usage && (
          <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3">
            <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-900/40">
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Credits remaining
              </p>
              <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-white">
                {usage.credits_remaining}
              </p>
            </div>
            <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-900/40">
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Reports this month
              </p>
              <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-white">
                {usage.reports_this_month}
                {usage.monthly_limit !== null && (
                  <span className="text-base font-normal text-slate-400">
                    /{usage.monthly_limit}
                  </span>
                )}
              </p>
            </div>
            <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-900/40">
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Resets on
              </p>
              <p className="mt-1 text-sm font-semibold text-slate-700 dark:text-slate-200">
                {usage.resets_on}
              </p>
            </div>
          </div>
        )}

        {/* Subscription dates */}
        {subscription && !isFree && (
          <div className="mt-4 flex flex-wrap gap-4 text-sm text-slate-600 dark:text-slate-300">
            <span className="flex items-center gap-1">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              Renews:{" "}
              <strong>
                {formatDate(subscription.current_period_end as number)}
              </strong>
            </span>
            {subscription.cancel_at_period_end && (
              <span className="flex items-center gap-1 text-amber-600 dark:text-amber-400">
                <AlertCircle className="h-4 w-4" />
                Cancels at period end
              </span>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="mt-6 flex flex-wrap gap-3">
          {!isFree && token && <ManagePortalButton token={token} />}
          {isFree && token && <UpgradePlanButton token={token} />}
        </div>
      </div>

      {/* Past-due warning */}
      {payment?.action_required && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 dark:border-amber-800/50 dark:bg-amber-950/30">
          <p className="flex items-center gap-2 font-semibold text-amber-700 dark:text-amber-400">
            <AlertCircle className="h-5 w-5" /> Payment action required
          </p>
          <p className="mt-1 text-sm text-amber-600 dark:text-amber-300">
            Your subscription is{" "}
            <strong>{payment.subscription_status}</strong>. Please update your
            payment method to avoid service interruption.
          </p>
          {token && (
            <div className="mt-3">
              <ManagePortalButton token={token} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
