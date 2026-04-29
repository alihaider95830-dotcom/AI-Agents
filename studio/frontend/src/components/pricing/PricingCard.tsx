import { Check } from "lucide-react";

import type { PricingPlan } from "@/components/pricing/pricingPlans";

interface PricingCardProps {
  plan: PricingPlan;
}

export function PricingCard({ plan }: PricingCardProps): JSX.Element {
  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm transition hover:shadow-md">
      <h3 className="text-xl font-semibold text-neutral-900">{plan.name}</h3>
      <p className="mt-2 text-sm text-neutral-600">{plan.summary}</p>
      <div className="mt-6 flex items-end gap-1">
        <span className="text-4xl font-semibold text-neutral-900">{plan.price}</span>
        <span className="pb-1 text-sm text-neutral-500">/mo</span>
      </div>
      <ul className="mt-6 space-y-3 text-sm text-neutral-700">
        {plan.features.map((feature) => (
          <li className="flex items-start gap-2" key={feature}>
            <Check className="mt-0.5 h-4 w-4 shrink-0 text-indigo-600" aria-hidden="true" />
            <span>{feature}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
