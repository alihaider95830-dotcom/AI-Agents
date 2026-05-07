import { PricingCard } from "@/components/pricing/PricingCard";
import { pricingPlans } from "@/components/pricing/pricingPlans";

export default function PricingSection(): JSX.Element {
  return (
    <section className="relative px-6 py-32 sm:py-48 overflow-hidden" aria-labelledby="pricing-heading">
      <div className="absolute inset-0 bg-white/[0.01] -z-10" />
      <div className="mx-auto w-full max-w-6xl text-center">
        <h2 id="pricing-heading" className="text-[34px] font-semibold text-white tracking-tight">
          Simple, transparent pricing
        </h2>
        <p className="mt-4 text-[16px] text-[var(--text-secondary)]">Start free. Upgrade when you need more.</p>

        <div className="mt-16 grid gap-6 md:grid-cols-3">
          {pricingPlans.map((plan) => (
            <PricingCard key={plan.name} plan={plan} />
          ))}
        </div>

        <p className="mt-10 text-[13px] text-[var(--text-tertiary)] uppercase tracking-[0.1em]">All plans include a 7-day money-back guarantee.</p>
      </div>
    </section>
  );
}
