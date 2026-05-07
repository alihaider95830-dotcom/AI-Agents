import { LoaderCircle } from "lucide-react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "destructive";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

const variantClasses: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary:
    "bg-white text-[#09090b] hover:bg-white/88 transform hover:-translate-y-[1px] active:translate-y-0",
  secondary:
    "bg-[var(--glass-surface)] border border-[var(--border-default)] text-[var(--text-primary)] hover:bg-[var(--glass-surface-hover)] hover:border-[var(--border-strong)]",
  ghost:
    "bg-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/04",
  destructive:
    "bg-red-500/12 border border-red-500/20 text-red-300 hover:bg-red-500/20",
};

const sizeClasses: Record<NonNullable<ButtonProps["size"]>, string> = {
  sm: "h-8 px-3 text-[11px] uppercase tracking-wider font-medium",
  md: "h-10 px-5 text-[14px] font-medium",
  lg: "h-12 px-8 text-[15px] font-medium",
};

export const Button = ({
  children,
  className,
  disabled = false,
  isLoading = false,
  size = "md",
  type = "button",
  variant = "primary",
  ...props
}: ButtonProps): JSX.Element => {
  const isDisabled = disabled || isLoading;

  return (
    <button
      className={[
        "inline-flex items-center justify-center gap-2 rounded-[var(--radius-md)] transition-all duration-200 ease-[var(--ease-out)]",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/30 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0a0a0b]",
        "disabled:cursor-not-allowed disabled:opacity-40",
        variantClasses[variant],
        sizeClasses[size],
        className ?? "",
      ].join(" ")}
      disabled={isDisabled}
      type={type}
      {...props}
    >
      {isLoading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
      <span>{children}</span>
    </button>
  );
};
