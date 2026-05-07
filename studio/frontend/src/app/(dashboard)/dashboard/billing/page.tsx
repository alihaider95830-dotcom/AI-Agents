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
      className="inline-flex items-center gap-2 rounded-full bg-zinc-900 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-zinc-800 disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
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
      Manage in Stripe
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
      className="inline-flex items-center gap-2 rounded-full border border-zinc-200 bg-white px-6 py-2.5 text-sm font-semibold text-zinc-900 transition hover:bg-zinc-50 disabled:opacity-60 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-100 dark:hover:bg-zinc-800"
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
        <Loader2 className="h-10 w-10 animate-spin text-zinc-900 dark:text-zinc-100" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-4 text-center">
        <div className="rounded-2xl bg-rose-50 p-4 dark:bg-rose-950/20">
          <AlertCircle className="h-8 w-8 text-rose-500" />
        </div>
        <p className="text-zinc-600 dark:text-zinc-400 font-medium">{error}</p>
      </div>
    );
  }

  const isFree = subscription?.status === "none";

  return (
    <div className="mx-auto max-w-3xl space-y-8 py-4">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-white">
          Billing & Subscription
        </h1>
        <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
          Manage your plan, credits, and payment method.
        </p>
      </div>

      {/* Plan overview */}
      <div className="rounded-[2.5rem] border border-zinc-200/60 bg-white/80 p-8 shadow-panel dark:border-zinc-800 dark:bg-zinc-950/80 sm:p-10">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-zinc-100 dark:bg-zinc-800">
              <CreditCard className="h-6 w-6 text-zinc-900 dark:text-zinc-100" />
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                Current Tier
              </p>
              <p className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-white">
                {usage ? tierLabel(usage.tier) : "—"}
              </p>
            </div>
          </div>
          <div className="flex self-start">
            {statusBadge(payment?.subscription_status)}
          </div>
        </div>

        {/* Credits */}
        {usage && (
          <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-2xl border border-zinc-100 bg-zinc-50/50 p-5 dark:border-zinc-800 dark:bg-zinc-900/40">
              <p className="text-xs font-bold uppercase tracking-wider text-zinc-400">
                Credits remaining
              </p>
              <p className="mt-2 text-3xl font-bold text-zinc-900 dark:text-white">
                {usage.credits_remaining}
              </p>
            </div>
            <div className="rounded-2xl border border-zinc-100 bg-zinc-50/50 p-5 dark:border-zinc-800 dark:bg-zinc-900/40">
              <p className="text-xs font-bold uppercase tracking-wider text-zinc-400">
                Reports this month
              </p>
              <p className="mt-2 text-3xl font-bold text-zinc-900 dark:text-white">
                {usage.reports_this_month}
                {usage.monthly_limit !== null && (
                  <span className="text-base font-medium text-zinc-400">
                    /{usage.monthly_limit}
                  </span>
                )}
              </p>
            </div>
            <div className="rounded-2xl border border-zinc-100 bg-zinc-50/50 p-5 dark:border-zinc-800 dark:bg-zinc-900/40">
              <p className="text-xs font-bold uppercase tracking-wider text-zinc-400">
                Usage Reset
              </p>
              <p className="mt-2 text-sm font-bold text-zinc-700 dark:text-zinc-200">
                {usage.resets_on}
              </p>
            </div>
          </div>
        )}

        {/* Subscription dates */}
        {subscription && !isFree && (
          <div className="mt-8 flex flex-wrap gap-6 text-sm">
            <span className="flex items-center gap-2 text-zinc-600 dark:text-zinc-400">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              <span className="font-medium">Renews:</span>
              <span className="font-bold text-zinc-900 dark:text-zinc-100">
                {formatDate(subscription.current_period_end as number)}
              </span>
            </span>
            {subscription.cancel_at_period_end && (
              <span className="flex items-center gap-2 text-rose-600 dark:text-rose-400">
                <AlertCircle className="h-4 w-4" />
                <span className="font-medium">Cancels at period end</span>
              </span>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="mt-10 flex flex-wrap gap-4">
          {!isFree && token && <ManagePortalButton token={token} />}
          {isFree && token && <UpgradePlanButton token={token} />}
        </div>
      </div>

      {/* Past-due warning */}
      {payment?.action_required && (
        <div className="rounded-3xl border border-rose-100 bg-rose-50/50 p-6 shadow-sm dark:border-rose-900/30 dark:bg-rose-950/20">
          <div className="flex items-start gap-4">
            <div className="rounded-full bg-rose-100 p-2 dark:bg-rose-900/50">
              <AlertCircle className="h-5 w-5 text-rose-600 dark:text-rose-400" />
            </div>
            <div>
              <p className="font-bold text-rose-900 dark:text-rose-100">Payment action required</p>
              <p className="mt-1 text-sm text-rose-700/80 dark:text-rose-300/80 leading-relaxed">
                Your subscription is currently <strong>{payment.subscription_status}</strong>. 
                Please update your payment method to avoid service interruption and maintain access to your reports.
              </p>
              {token && (
                <div className="mt-5">
                  <ManagePortalButton token={token} />
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
