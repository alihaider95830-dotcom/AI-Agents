interface BadgeProps {
  variant?: "free" | "pro" | "agency" | "default";
  children: React.ReactNode;
  className?: string;
}

const badgeClasses: Record<NonNullable<BadgeProps["variant"]>, string> = {
  free: "bg-white/05 text-[var(--text-secondary)] border-white/10",
  pro: "bg-white text-[var(--text-inverse)] border-white",
  agency: "bg-white/10 text-white border-white/20 shadow-[0_0_15px_-3px_rgba(255,255,255,0.1)]",
  default: "bg-white/06 text-[var(--text-secondary)] border-white/10",
};

export const Badge = ({
  children,
  className,
  variant = "default",
}: BadgeProps): JSX.Element => {
  return (
    <span
      className={[
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-[0.06em] backdrop-blur-sm",
        badgeClasses[variant],
        className ?? "",
      ].join(" ")}
    >
      {children}
    </span>
  );
};
