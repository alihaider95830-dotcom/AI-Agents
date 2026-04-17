"use client";

import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/Button";
import { REPORT_TYPE_OPTIONS, type ReportType } from "@/types/jobs";

interface TopicFormProps {
  onSubmit: (topic: string, report_type: ReportType) => void | Promise<void>;
  isLoading: boolean;
  creditsRemaining: number;
}

const topicFormSchema = z.object({
  topic: z
    .string()
    .min(10, "Topic must be at least 10 characters.")
    .max(500, "Topic must be 500 characters or fewer."),
  report_type: z.enum([
    "analytical",
    "informational",
    "comparative",
    "argumentative",
  ]),
});

type TopicFormValues = z.infer<typeof topicFormSchema>;

export const TopicForm = ({
  onSubmit,
  isLoading,
  creditsRemaining,
}: TopicFormProps): JSX.Element => {
  const {
    formState: { errors },
    handleSubmit,
    register,
    watch,
  } = useForm<TopicFormValues>({
    defaultValues: {
      topic: "",
      report_type: "analytical",
    },
    resolver: zodResolver(topicFormSchema),
  });

  const topic = watch("topic", "");

  const handleFormSubmit = handleSubmit(async (values) => {
    await onSubmit(values.topic, values.report_type);
  });

  return (
    <form
      className="rounded-[1.75rem] border border-slate-200/70 bg-white/85 p-6 shadow-panel transition-all duration-300 dark:border-slate-800 dark:bg-slate-950/80 sm:p-8"
      onSubmit={handleFormSubmit}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-brand-ocean dark:text-brand-gold">
            Start a report
          </p>
          <h1 className="mt-2 font-[var(--font-heading)] text-3xl font-semibold text-slate-900 dark:text-white">
            Tell the crew what to research
          </h1>
        </div>
        <p className="rounded-full bg-brand-mist px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-brand-ink dark:bg-slate-800 dark:text-slate-100">
          {creditsRemaining} credits left
        </p>
      </div>

      <div className="mt-8">
        <label
          className="flex flex-col gap-2 text-sm font-medium text-slate-700 dark:text-slate-200"
          htmlFor="topic"
        >
          <span>Topic</span>
          <textarea
            className={[
              "min-h-[180px] rounded-[1.5rem] border bg-white/90 px-4 py-4 text-sm text-slate-900 shadow-sm outline-none transition-all",
              "placeholder:text-slate-400 focus:border-brand-ocean focus:ring-2 focus:ring-brand-ocean/20",
              "dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-100 dark:placeholder:text-slate-500",
              errors.topic
                ? "border-rose-500 focus:border-rose-500 focus:ring-rose-500/20"
                : "border-slate-200",
            ].join(" ")}
            id="topic"
            maxLength={500}
            placeholder="e.g. The future of renewable energy in Southeast Asia"
            {...register("topic")}
          />
        </label>
        <div className="mt-2 flex items-center justify-between text-xs">
          <span className="font-medium text-rose-500">{errors.topic?.message}</span>
          <span className="text-slate-500 dark:text-slate-400">
            {topic.length}/500
          </span>
        </div>
      </div>

      <fieldset className="mt-8">
        <legend className="text-sm font-medium text-slate-700 dark:text-slate-200">
          Report type
        </legend>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          {REPORT_TYPE_OPTIONS.map((option) => (
            <label
              key={option.value}
              className="cursor-pointer"
              htmlFor={option.value}
            >
              <input
                className="peer sr-only"
                id={option.value}
                type="radio"
                value={option.value}
                {...register("report_type")}
              />
              <div className="rounded-2xl border border-slate-200 bg-white/90 p-4 text-sm font-medium text-slate-600 transition-all duration-200 peer-checked:border-brand-ocean peer-checked:bg-brand-mist peer-checked:text-brand-ink peer-focus-visible:ring-2 peer-focus-visible:ring-brand-ocean/30 dark:border-slate-800 dark:bg-slate-900/80 dark:text-slate-300 dark:peer-checked:border-brand-gold dark:peer-checked:bg-slate-800 dark:peer-checked:text-white">
                {option.label}
              </div>
            </label>
          ))}
        </div>
        {errors.report_type?.message ? (
          <p className="mt-2 text-xs font-medium text-rose-500">
            {errors.report_type.message}
          </p>
        ) : null}
      </fieldset>

      <div className="mt-8 space-y-3">
        <Button
          className="w-full sm:w-auto"
          disabled={creditsRemaining === 0}
          isLoading={isLoading}
          size="lg"
          type="submit"
        >
          {isLoading ? "Generating..." : "Generate Report"}
        </Button>
        {creditsRemaining === 0 ? (
          <p className="text-sm font-medium text-amber-600 dark:text-amber-300">
            No credits remaining
          </p>
        ) : null}
      </div>
    </form>
  );
};
