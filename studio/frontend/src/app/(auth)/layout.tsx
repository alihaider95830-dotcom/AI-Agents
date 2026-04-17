interface AuthLayoutProps {
  children: React.ReactNode;
}

export default function AuthLayout({
  children,
}: AuthLayoutProps): JSX.Element {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(212,163,115,0.28),transparent_28%),radial-gradient(circle_at_bottom_right,rgba(43,95,117,0.22),transparent_26%)]" />
      <div className="relative grid w-full max-w-5xl overflow-hidden rounded-[2rem] border border-white/50 bg-white/70 shadow-panel backdrop-blur-2xl dark:border-slate-800/80 dark:bg-slate-950/75 md:grid-cols-[1.05fr_0.95fr]">
        <div className="hidden flex-col justify-between bg-brand-ink p-10 text-white md:flex">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-white/60">
              Report Forge
            </p>
            <h1 className="mt-5 max-w-sm font-[var(--font-heading)] text-4xl font-semibold leading-tight">
              Turn research prompts into polished reports with an AI crew.
            </h1>
            <p className="mt-5 max-w-md text-sm leading-7 text-white/75">
              Sign in to launch research, planning, writing, and QA from one
              streamlined workspace built for teams shipping client-ready
              insight.
            </p>
          </div>
          <div className="space-y-3 text-sm text-white/70">
            <p>Real-time report generation</p>
            <p>Structured exports for PDF and Markdown</p>
            <p>Usage tiers for teams of every size</p>
          </div>
        </div>

        <div className="flex min-h-[720px] items-center justify-center p-6 sm:p-10">
          <div className="w-full max-w-md">{children}</div>
        </div>
      </div>
    </div>
  );
}
