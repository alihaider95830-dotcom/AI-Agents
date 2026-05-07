const stats = [
  { value: "500+", label: "reports generated" },
  { value: "12", label: "sources per report" },
  { value: "< 90 sec", label: "avg. generation" },
  { value: "4", label: "AI agents per report" },
];

export default function SocialProofBar(): JSX.Element {
  return (
    <section className="px-6">
      <div className="mx-auto w-full max-w-6xl glass-card !bg-white/[0.01] p-10 md:p-14 border-white/[0.05]">
        <div className="flex flex-col gap-12 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-md">
            <p className="text-[11px] font-bold uppercase tracking-[0.4em] text-white/40">
              PERFORMANCE METRICS
            </p>
            <h2 className="mt-6 text-[28px] font-semibold tracking-tight text-white leading-[1.2]">
              Real output, real speed, <br className="hidden sm:block"/> real citations.
            </h2>
          </div>
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4 lg:flex-1 lg:justify-end">
            {stats.map((stat) => (
              <div
                key={stat.label}
                className="flex flex-col gap-2"
              >
                <p className="text-[36px] font-bold tracking-tight text-white font-mono drop-shadow-[0_0_15px_rgba(255,255,255,0.1)]">
                  {stat.value}
                </p>
                <p className="text-[12px] font-medium uppercase tracking-widest text-[var(--text-secondary)]">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

