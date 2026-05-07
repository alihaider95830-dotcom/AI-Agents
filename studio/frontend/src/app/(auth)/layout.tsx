interface AuthLayoutProps {
  children: React.ReactNode;
}

export default function AuthLayout({
  children,
}: AuthLayoutProps): JSX.Element {
  return (
    <div className="relative flex min-h-screen items-center justify-center px-4 py-10">
      <div className="relative grid w-full max-w-5xl overflow-hidden glass-elevated !bg-white/[0.03] shadow-2xl md:grid-cols-[1.05fr_0.95fr] animate-glass-enter">
        <div className="hidden flex-col justify-between bg-white/[0.02] border-r border-white/05 p-12 text-white md:flex">
          <div>
            <div className="flex items-center gap-3 text-[18px] font-semibold tracking-tight text-white">
              <div className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-md)] bg-white text-[var(--text-inverse)] shadow-lg shadow-white/10">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 2 22 22 22"></polygon></svg>
              </div>
              Studio
            </div>
            <h1 className="mt-12 max-w-sm text-[34px] font-semibold leading-[1.2] tracking-tight">
              Turn research prompts into polished reports <br/>
              <span className="text-[var(--text-secondary)] opacity-50">with an AI crew.</span>
            </h1>
            <p className="mt-8 max-w-md text-[15px] leading-relaxed text-[var(--text-secondary)]">
              Sign in to launch research, planning, writing, and QA from one
              streamlined workspace built for teams shipping client-ready
              insight.
            </p>
          </div>
          <div className="space-y-6 text-[13px] text-[var(--text-tertiary)] uppercase tracking-wider font-medium">
            <div className="flex items-center gap-4">
              <div className="h-1.5 w-1.5 rounded-full bg-white/20"></div>
              <p>Real-time report generation</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="h-1.5 w-1.5 rounded-full bg-white/20"></div>
              <p>Structured exports for PDF and Markdown</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="h-1.5 w-1.5 rounded-full bg-white/20"></div>
              <p>Usage tiers for teams of every size</p>
            </div>
          </div>
        </div>

        <div className="flex min-h-[720px] items-center justify-center p-8 sm:p-12">
          <div className="w-full max-w-md">{children}</div>
        </div>
      </div>
    </div>
  );
}
