import Link from "next/link";
import { Star } from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function CtaSection(): JSX.Element {
  return (
    <section className="px-6 py-32 sm:py-40">
      <div className="mx-auto w-full max-w-5xl relative">
        {/* Local Ambient Glow */}
        <div className="absolute inset-0 -z-10 bg-white/[0.02] blur-3xl rounded-[3rem]" />
        
        <div className="glass-elevated !bg-white/[0.05] border-white/20 px-8 py-24 sm:py-28 text-center shadow-2xl sm:px-12 animate-glass-enter">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/05 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.1em] text-[var(--text-secondary)] backdrop-blur-sm">
            Ready when you are
          </span>
          <h2 className="mt-10 text-[36px] font-semibold tracking-tight text-white sm:text-[52px] leading-tight">
            Start generating in <span className="opacity-60 font-light">30 seconds.</span>
          </h2>
          <p className="mx-auto mt-8 max-w-2xl text-[17px] sm:text-[18px] leading-relaxed text-[var(--text-secondary)] font-light">
            No credit card. No setup. Just paste a topic and let the crew do the work.
            Join hundreds of researchers shipping faster today.
          </p>

          <div className="mt-14 flex flex-col items-center justify-center gap-4">
            <Link href="/auth/signup" passHref legacyBehavior>
              <Button 
                size="lg" 
                className="w-full sm:w-auto !rounded-full !h-[56px] px-16 bg-white text-black hover:bg-white/95 shadow-[0_12px_32px_rgba(255,255,255,0.25)] hover:shadow-[0_16px_48px_rgba(255,255,255,0.35)] transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] font-bold text-[15px] sm:text-[16px]"
              >
                Generate your first report
              </Button>
            </Link>
          </div>
          
          <div className="mt-8 inline-flex items-center gap-2 rounded-full border border-emerald-500/35 bg-emerald-500/[0.1] px-5 py-3 backdrop-blur-md hover:border-emerald-500/45 hover:bg-emerald-500/[0.14] transition-all duration-300">
            <Star className="h-4 w-4 text-emerald-400 fill-emerald-400" />
            <p className="text-[13px] sm:text-[14px] font-semibold text-emerald-300">
              Free forever · No credit card required · 2 reports per month
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
