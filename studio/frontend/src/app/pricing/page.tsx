import Link from "next/link";

import { PricingCard } from "@/components/pricing/PricingCard";
import { pricingPlans } from "@/components/pricing/pricingPlans";

export default function PricingPage(): JSX.Element {
  return (
    <main className="min-h-screen bg-slate-50 px-6 py-12 text-slate-950">
      <div className="mx-auto max-w-6xl">
        <div className="max-w-2xl">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand-ocean">
            Studio Pricing
          </p>
          <h1 className="mt-3 text-4xl font-semibold tracking-normal">
            Choose the report capacity that fits your workflow.
          </h1>
          <p className="mt-4 text-base text-slate-600">
            Start small, then upgrade when your research cadence needs more
            credits and export options.
          </p>
        </div>

        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {pricingPlans.map((plan) => (
            <PricingCard key={plan.name} plan={plan} />
          ))}
        </div>

        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            className="inline-flex h-10 items-center justify-center rounded-lg bg-brand-ocean px-4 text-sm font-medium text-white transition hover:bg-brand-ocean/90"
            href="/auth/signup"
          >
            Create account
          </Link>
          <Link
            className="inline-flex h-10 items-center justify-center rounded-lg border border-slate-300 px-4 text-sm font-medium text-slate-800 transition hover:bg-white"
            href="/auth/signin"
          >
            Sign in
          </Link>
        </div>
      </div>
    </main>
  );
}
