import { PricingCard } from "@/components/pricing/PricingCard";
import { pricingPlans } from "@/components/pricing/pricingPlans";

export default function PricingSection(): JSX.Element {
  return (
    <section className="px-4 py-16 sm:px-6" aria-labelledby="pricing-heading">
      <div className="mx-auto w-full max-w-6xl text-center">
        <h2 id="pricing-heading" className="text-3xl font-semibold text-neutral-900">
          Simple, transparent pricing
        </h2>
        <p className="mt-2 text-neutral-600">Start free. Upgrade when you need more.</p>

        <div className="mt-10 grid gap-5 md:grid-cols-3">
          {pricingPlans.map((plan) => (
            <PricingCard key={plan.name} plan={plan} />
          ))}
        </div>

        <p className="mt-6 text-sm text-neutral-500">All plans include a 7-day money-back guarantee.</p>
      </div>
    </section>
  );
}
