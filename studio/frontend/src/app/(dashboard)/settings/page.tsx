export default function SettingsPage(): JSX.Element {
  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-[26px] font-semibold tracking-tight text-white">
            Workspace Settings
          </h1>
          <p className="mt-2 text-[15px] text-[var(--text-secondary)]">
            Manage your profile, billing, and workspace preferences.
          </p>
        </div>
      </div>

      <section className="glass-card p-10 bg-white/[0.02]">
        <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/05 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.1em] text-[var(--text-secondary)] backdrop-blur-sm">
          Coming Soon
        </span>
        <h2 className="mt-6 text-[20px] font-semibold tracking-tight text-white">
          Workspace controls are being polished
        </h2>
        <p className="mt-4 max-w-2xl text-[15px] leading-relaxed text-[var(--text-secondary)]">
          Billing controls, profile management, and detailed workspace preferences will
          slot into this protected route in the next update.
        </p>
        
        <div className="mt-12 grid gap-4 sm:grid-cols-2">
          <div className="rounded-[var(--radius-lg)] border border-white/05 bg-white/02 p-6">
            <h3 className="text-[15px] font-semibold text-white">Billing & Subscription</h3>
            <p className="mt-2 text-[13px] text-[var(--text-tertiary)]">Manage your plan and invoices.</p>
          </div>
          <div className="rounded-[var(--radius-lg)] border border-white/05 bg-white/02 p-6">
            <h3 className="text-[15px] font-semibold text-white">Profile Settings</h3>
            <p className="mt-2 text-[13px] text-[var(--text-tertiary)]">Update your email and password.</p>
          </div>
        </div>
      </section>
    </div>
  );
}
