import NavBar from "@/components/landing/NavBar";
import Footer from "@/components/landing/Footer";
import { PricingCard } from "@/components/pricing/PricingCard";
import { pricingPlans } from "@/components/pricing/pricingPlans";
import { Button } from "@/components/ui/Button";

export default function PricingPage(): JSX.Element {
  return (
    <main className="text-[var(--text-primary)]">
      <NavBar />
      
      <section className="px-6 py-24 sm:py-32 lg:py-40">
        <div className="mx-auto max-w-6xl">
          <div className="max-w-2xl animate-glass-enter">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/05 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.1em] text-[var(--text-secondary)] backdrop-blur-sm">
              <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-white animate-pulse" />
              Simple pricing
            </span>
            <h1 className="mt-8 text-[40px] font-semibold tracking-tight text-white sm:text-[52px] leading-[1.1]">
              Choose the report capacity <br className="hidden sm:block"/>
              <span className="text-[var(--text-secondary)] opacity-50">that fits your workflow.</span>
            </h1>
            <p className="mt-8 text-[16px] leading-relaxed text-[var(--text-secondary)] sm:text-[18px]">
              Start small, then upgrade when your research cadence needs more
              credits and export options. Every plan includes our full agent crew.
            </p>
          </div>

          <div className="mt-20 grid gap-8 md:grid-cols-3">
            {pricingPlans.map((plan) => (
              <PricingCard key={plan.name} plan={plan} />
            ))}
          </div>

          <div className="mt-24 glass-card p-12 text-center bg-white/[0.02]">
            <h3 className="text-[20px] font-semibold text-white">Need a custom plan?</h3>
            <p className="mt-2 text-[15px] text-[var(--text-secondary)] max-w-md mx-auto">Contact us for enterprise-grade research capacity and custom agent configurations.</p>
            <a href="mailto:hello@yourdomain.com">
              <Button
                variant="primary"
                className="mt-8 !rounded-full px-10"
              >
                Talk to sales
              </Button>
            </a>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
