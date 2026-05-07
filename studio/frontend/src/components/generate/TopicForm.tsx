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
      className="glass-card p-10 bg-white/[0.03] border-white/05 transition-all duration-500 relative overflow-hidden glass-scanline"
      onSubmit={handleFormSubmit}
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between relative z-10">
        <div>
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/05 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.15em] text-[var(--text-secondary)] backdrop-blur-sm">
            MISSION_CONTROL
          </span>
          <h1 className="mt-6 text-[38px] font-bold tracking-tight text-white leading-[1.1]">
            Research Initialization
          </h1>
        </div>
      </div>

      <div className="mt-12 relative z-10">
        <label
          className="ml-1 text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--text-tertiary)] font-mono"
          htmlFor="topic"
        >
          INPUT_TARGET_SPECIFICATION
        </label>
        <textarea
          className={[
            "mt-4 min-h-[180px] w-full rounded-[var(--radius-lg)] border border-white/05 bg-black/40 px-6 py-5 text-[16px] text-white outline-none transition-all duration-300 shadow-[inset_0_2px_10px_rgba(0,0,0,0.2)]",
            "placeholder:text-[var(--text-tertiary)] placeholder:opacity-50 focus:border-white/20 focus:shadow-[0_0_0_4px_rgba(255,255,255,0.02)]",
            errors.topic
              ? "border-red-500/20 focus:border-red-500/40"
              : "",
          ].join(" ")}
          id="topic"
          maxLength={500}
          placeholder="Enter objective parameters (e.g. Analysis of Quantum Computing Scalability in 2026)..."
          {...register("topic")}
        />
        <div className="mt-4 flex items-center justify-between text-[10px] font-bold tracking-[0.1em] font-mono">
          <span className="text-red-400/60 uppercase">{errors.topic?.message}</span>
          <span className="text-[var(--text-tertiary)] uppercase opacity-60">
            BUFFER: {topic.length} / 500
          </span>
        </div>
      </div>

      <fieldset className="mt-14 relative z-10">
        <legend className="ml-1 text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--text-tertiary)] font-mono">
          ANALYSIS_PROTOCOL_LENS
        </legend>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {REPORT_TYPE_OPTIONS.map((option) => (
            <label
              key={option.value}
              className="cursor-pointer group"
              htmlFor={option.value}
            >
              <input
                className="peer sr-only"
                id={option.value}
                type="radio"
                value={option.value}
                {...register("report_type")}
              />
              <div className="flex h-full flex-col rounded-[var(--radius-md)] border border-white/05 bg-white/02 p-6 transition-all duration-500 peer-checked:bg-white peer-checked:border-white group-hover:border-white/10 group-hover:bg-white/05 shadow-[inset_0_1px_0_rgba(255,255,255,0.02)]">
                <span className="text-[14px] font-bold capitalize text-white peer-checked:text-black transition-colors">
                  {option.label}
                </span>
                <span className="mt-2 text-[10px] font-bold text-[var(--text-tertiary)] peer-checked:text-black/60 transition-colors uppercase tracking-widest font-mono">
                  {option.value}_MODE
                </span>
              </div>
            </label>
          ))}
        </div>
      </fieldset>

      <div className="mt-16 flex flex-col items-center gap-8 sm:flex-row relative z-10">
        <Button
          className="h-14 px-16 !rounded-full text-[16px] font-bold btn-glow shadow-[0_0_30px_rgba(255,255,255,0.1)] hover:shadow-[0_0_50px_rgba(255,255,255,0.2)]"
          disabled={creditsRemaining === 0}
          isLoading={isLoading}
          type="submit"
          variant="primary"
        >
          {isLoading ? "INITIATING_PROTOCOL..." : "LAUNCH_RESEARCH_CREW"}
        </Button>
        {creditsRemaining === 0 && (
          <p className="text-[12px] font-bold text-red-400 uppercase tracking-widest font-mono">
            STATUS: INSUFFICIENT_CREDITS
          </p>
        )}
      </div>
    </form>
  );
};
