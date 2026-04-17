export default function SettingsPage(): JSX.Element {
  return (
    <section className="rounded-[2rem] border border-slate-200/70 bg-white/80 p-8 shadow-panel dark:border-slate-800 dark:bg-slate-900/80">
      <p className="text-xs uppercase tracking-[0.35em] text-brand-ocean dark:text-brand-gold">
        Settings
      </p>
      <h1 className="mt-3 font-[var(--font-heading)] text-3xl font-semibold text-slate-900 dark:text-white">
        M16+ will go here
      </h1>
      <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
        Billing controls, profile management, and workspace preferences will
        slot into this protected route next.
      </p>
    </section>
  );
}
