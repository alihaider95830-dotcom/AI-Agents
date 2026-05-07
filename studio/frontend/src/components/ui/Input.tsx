import type { HTMLInputTypeAttribute } from "react";
import type { UseFormRegisterReturn } from "react-hook-form";

interface InputProps {
  label: string;
  error?: string;
  type?: HTMLInputTypeAttribute;
  placeholder?: string;
  register: UseFormRegisterReturn;
  autoComplete?: string;
  id?: string;
}

export const Input = ({
  autoComplete,
  error,
  label,
  placeholder,
  register,
  type = "text",
  id,
}: InputProps): JSX.Element => {
  return (
    <label className="flex w-full flex-col gap-2 text-[13px] font-medium text-[var(--text-secondary)]">
      <span className="ml-1 uppercase tracking-wider text-[11px] text-[var(--text-tertiary)]">{label}</span>
      <input
        autoComplete={autoComplete}
        className={[
          "h-11 rounded-[var(--radius-md)] border border-[var(--border-input)] bg-[var(--glass-surface)] px-4 text-[14px] text-[var(--text-primary)] outline-none transition-all duration-200",
          "placeholder:text-[var(--text-tertiary)] focus:border-white/30 focus:shadow-[0_0_0_3px_rgba(255,255,255,0.06)]",
          error
            ? "border-red-500/40 focus:border-red-500/50 focus:shadow-[0_0_0_3px_rgba(239,68,68,0.08)]"
            : "",
        ].join(" ")}
        placeholder={placeholder}
        id={id}
        type={type}
        {...register}
      />
      {error ? (
        <span className="ml-1 text-[11px] font-medium text-red-400/80 uppercase tracking-tight">{error}</span>
      ) : null}
    </label>
  );
};
