import { Check } from "lucide-react";
import Link from "next/link";

import type { PricingPlan } from "@/components/pricing/pricingPlans";
import { Button } from "@/components/ui/Button";

interface PricingCardProps {
  plan: PricingPlan;
}

export function PricingCard({ plan }: PricingCardProps): JSX.Element {
  const isPro = plan.name.toLowerCase() === "pro";

  return (
    <section 
      className={[
        "relative flex flex-col p-8 transition-all duration-500",
        isPro 
          ? "glass-elevated !bg-white/[0.08] scale-105 z-10 border-white/20" 
          : "glass-card !bg-white/[0.03] hover:!bg-white/[0.06]"
      ].join(" ")}
    >
      {isPro && (
        <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-white px-3 py-1 text-[10px] font-bold uppercase tracking-[0.15em] text-[var(--text-inverse)] border border-white">
          Most Popular
        </span>
      )}

      <h3 className="text-[20px] font-semibold text-white tracking-tight">{plan.name}</h3>
      <p className="mt-2 text-[14px] text-[var(--text-secondary)]">
        {plan.summary}
      </p>
      
      <div className="mt-8 flex items-end gap-1">
        <span className="text-display text-[42px] font-bold tracking-tight text-white">{plan.price}</span>
        <span className="pb-2 text-[13px] font-medium text-[var(--text-tertiary)] uppercase tracking-wide">
          /mo
        </span>
      </div>

      <Link href="/auth/signup" passHref legacyBehavior>
        <Button
          variant={isPro ? "primary" : "secondary"}
          className="mt-10 !rounded-full py-6 text-[15px]"
        >
          Get started
        </Button>
      </Link>

      <ul className="mt-12 space-y-5 text-[14px]">
        {plan.features.map((feature) => (
          <li className="flex items-start gap-3" key={feature}>
            <Check 
              className="mt-0.5 h-4 w-4 shrink-0 text-white/40" 
              aria-hidden="true" 
            />
            <span className="text-[var(--text-secondary)] leading-tight">{feature}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
