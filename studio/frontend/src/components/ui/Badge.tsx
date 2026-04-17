interface BadgeProps {
  variant?: "free" | "pro" | "agency" | "default";
  children: React.ReactNode;
}

const badgeClasses: Record<NonNullable<BadgeProps["variant"]>, string> = {
  free: "bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-200",
  pro: "bg-sky-100 text-sky-700 dark:bg-sky-900/60 dark:text-sky-200",
  agency:
    "bg-amber-100 text-amber-700 dark:bg-amber-900/60 dark:text-amber-200",
  default:
    "bg-brand-mist text-brand-ink dark:bg-slate-800 dark:text-slate-100",
};

export const Badge = ({
  children,
  variant = "default",
}: BadgeProps): JSX.Element => {
  return (
    <span
      className={[
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold uppercase tracking-wide",
        badgeClasses[variant],
      ].join(" ")}
    >
      {children}
    </span>
  );
};
