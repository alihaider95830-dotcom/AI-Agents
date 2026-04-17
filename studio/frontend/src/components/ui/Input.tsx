import type { HTMLInputTypeAttribute } from "react";
import type { UseFormRegisterReturn } from "react-hook-form";

interface InputProps {
  label: string;
  error?: string;
  type?: HTMLInputTypeAttribute;
  placeholder?: string;
  register: UseFormRegisterReturn;
  autoComplete?: string;
}

export const Input = ({
  autoComplete,
  error,
  label,
  placeholder,
  register,
  type = "text",
}: InputProps): JSX.Element => {
  return (
    <label className="flex w-full flex-col gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
      <span>{label}</span>
      <input
        autoComplete={autoComplete}
        className={[
          "h-11 rounded-xl border bg-white/90 px-3 text-sm text-slate-900 shadow-sm outline-none transition-all",
          "placeholder:text-slate-400 focus:border-brand-ocean focus:ring-2 focus:ring-brand-ocean/20",
          "dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-100 dark:placeholder:text-slate-500",
          error
            ? "border-rose-500 focus:border-rose-500 focus:ring-rose-500/20"
            : "border-slate-200",
        ].join(" ")}
        placeholder={placeholder}
        type={type}
        {...register}
      />
      {error ? (
        <span className="text-xs font-medium text-rose-500">{error}</span>
      ) : null}
    </label>
  );
};
