import { Database, FileText, Globe, Lock, RefreshCw, Zap } from "lucide-react";

const features = [
  {
    icon: Globe,
    title: "Live web research",
    description: "Agents search the live web - no stale training data.",
  },
  {
    icon: Database,
    title: "Vector knowledge base",
    description: "Research is embedded and indexed so every claim is traceable.",
  },
  {
    icon: FileText,
    title: "PDF + Markdown export",
    description: "Download your report as a beautifully formatted PDF or raw markdown.",
  },
  {
    icon: Zap,
    title: "Under 90 seconds",
    description: "The full pipeline - research to final copy - completes in under 90 seconds.",
  },
  {
    icon: RefreshCw,
    title: "Fact-checked output",
    description: "A dedicated QA agent cross-references every claim before you see it.",
  },
  {
    icon: Lock,
    title: "Your data stays yours",
    description: "Reports are private to your account. We never train on your content.",
  },
];

export default function FeaturesSection(): JSX.Element {
  return (
    <section id="features" className="px-6" aria-labelledby="features-heading">
      <div className="mx-auto w-full max-w-6xl">
        <div className="max-w-3xl animate-glass-enter">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/05 px-4 py-1.5 text-[11px] font-bold uppercase tracking-[0.2em] text-white/40 backdrop-blur-sm">
            PRODUCT HIGHLIGHTS
          </span>
          <h2 id="features-heading" className="mt-10 text-[38px] font-semibold tracking-tight text-white sm:text-[48px] leading-[1.1]">
            Everything you need. <br className="hidden sm:block"/> Nothing you don&apos;t.
          </h2>
          <p className="mt-6 text-[17px] leading-relaxed text-[var(--text-secondary)] sm:text-[19px] max-w-2xl font-light">
            Studio combines live research, structured synthesis, and clean exports into one flow that feels intentional and fast.
          </p>
        </div>

        <div className="mt-20 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <article
                key={feature.title}
                className="group glass-card p-10 bg-white/[0.01] hover:bg-white/[0.04] transition-all duration-500 border-white/[0.05] hover:border-white/10"
              >
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/[0.03] text-white border border-white/10 shadow-xl transition-all duration-500 group-hover:scale-110 group-hover:bg-white group-hover:text-black">
                  <Icon className="h-6 w-6" aria-hidden="true" />
                </div>
                <h3 className="mt-8 text-[19px] font-semibold tracking-tight text-white">
                  {feature.title}
                </h3>
                <p className="mt-4 text-[15px] leading-relaxed text-[var(--text-secondary)] font-light">
                  {feature.description}
                </p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}

