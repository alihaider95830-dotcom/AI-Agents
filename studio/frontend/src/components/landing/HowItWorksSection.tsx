import { LayoutList, PenLine, Search, ShieldCheck } from "lucide-react";

const steps = [
  {
    icon: Search,
    name: "Researcher",
    description:
      "Searches 8-12 live sources and indexes key facts, statistics, and competitor mentions.",
  },
  {
    icon: LayoutList,
    name: "Planner",
    description:
      "Reads the research and builds a structured outline with arguments for each section.",
  },
  {
    icon: PenLine,
    name: "Writer",
    description:
      "Drafts the full report with inline citations, professional tone, and clean markdown formatting.",
  },
  {
    icon: ShieldCheck,
    name: "QA Specialist",
    description:
      "Cross-references every claim against the source list, fixes inconsistencies, and polishes the final copy.",
  },
];

export default function HowItWorksSection(): JSX.Element {
  return (
    <section className="relative px-6 overflow-hidden" aria-labelledby="how-it-works-heading">
      <div className="mx-auto w-full max-w-6xl">
        <div className="mx-auto max-w-2xl text-center animate-glass-enter">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/05 px-4 py-1.5 text-[11px] font-bold uppercase tracking-[0.2em] text-white/40 backdrop-blur-sm">
            HOW IT WORKS
          </span>
          <h2 id="how-it-works-heading" className="mt-10 text-[38px] font-semibold tracking-tight text-white sm:text-[48px] leading-[1.1]">
            Four agents. One pipeline.
          </h2>
          <p className="mt-6 text-[17px] leading-relaxed text-[var(--text-secondary)] sm:text-[19px] font-light">
            Each step is visible and structured so the pipeline feels fast, transparent, and trustworthy.
          </p>
        </div>

        <div className="mt-24 grid gap-10 md:grid-cols-4">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <article key={step.name} className="relative group">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white text-[16px] font-bold text-black shadow-[0_0_20px_rgba(255,255,255,0.2)] mb-8 md:mx-auto transition-transform group-hover:scale-110">
                  {index + 1}
                </div>

                <div className="glass-card p-10 bg-white/[0.01] hover:bg-white/[0.04] transition-all duration-500 h-full md:text-center border-white/[0.05] hover:border-white/10">
                  <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-white/[0.03] text-white border border-white/10 mb-8 md:mx-auto group-hover:scale-110 group-hover:bg-white group-hover:text-black transition-all duration-500">
                    <Icon className="h-6 w-6" aria-hidden="true" />
                  </div>
                  <h3 className="text-[19px] font-semibold tracking-tight text-white">
                    {step.name}
                  </h3>
                  <p className="mt-4 text-[15px] leading-relaxed text-[var(--text-secondary)] font-light">
                    {step.description}
                  </p>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}

