import {
  CheckCircle2,
  Map,
  PenLine,
  Search,
  ShieldCheck,
} from "lucide-react";

import type { JobLifecycleStatus } from "@/types/jobs";

interface AgentStatusBarProps {
  currentStage: string;
  progress_pct: number;
}

type AgentVisualStatus = "waiting" | "active" | "complete";

interface AgentStep {
  key: Exclude<JobLifecycleStatus, "queued" | "complete" | "failed">;
  label: string;
  icon: typeof Search;
}

const agentSteps: AgentStep[] = [
  { key: "researching", label: "Researcher", icon: Search },
  { key: "planning", label: "Planner", icon: Map },
  { key: "writing", label: "Writer", icon: PenLine },
  { key: "qa", label: "QA", icon: ShieldCheck },
];

const stageOrder: Record<AgentStep["key"], number> = {
  researching: 0,
  planning: 1,
  writing: 2,
  qa: 3,
};

const statusClasses: Record<AgentVisualStatus, string> = {
  waiting:
    "border-slate-200 bg-white/80 text-slate-400 dark:border-slate-800 dark:bg-slate-900/70 dark:text-slate-500",
  active:
    "border-sky-200 bg-sky-50 text-sky-700 animate-pulse dark:border-sky-900/80 dark:bg-sky-950/40 dark:text-sky-200",
  complete:
    "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/80 dark:bg-emerald-950/40 dark:text-emerald-200",
};

const getAgentStatus = (
  agentKey: AgentStep["key"],
  currentStage: string,
): AgentVisualStatus => {
  if (currentStage === "complete") {
    return "complete";
  }

  if (!(currentStage in stageOrder)) {
    return "waiting";
  }

  const currentStageIndex = stageOrder[currentStage as AgentStep["key"]];
  const agentIndex = stageOrder[agentKey];

  if (agentIndex < currentStageIndex) {
    return "complete";
  }

  if (agentIndex === currentStageIndex) {
    return "active";
  }

  return "waiting";
};

export const AgentStatusBar = ({
  currentStage,
  progress_pct,
}: AgentStatusBarProps): JSX.Element => {
  const clampedProgress = Math.min(Math.max(progress_pct, 0), 100);

  return (
    <section className="rounded-[1.75rem] border border-slate-200/70 bg-white/85 p-5 shadow-panel transition-all duration-300 dark:border-slate-800 dark:bg-slate-950/80">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-brand-ocean dark:text-brand-gold">
            Agent pipeline
          </p>
          <h2 className="mt-2 font-[var(--font-heading)] text-2xl font-semibold text-slate-900 dark:text-white">
            Live crew progress
          </h2>
        </div>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          {clampedProgress}% complete
        </p>
      </div>

      <div className="mt-6 grid gap-3 md:grid-cols-4">
        {agentSteps.map((step) => {
          const Icon = step.icon;
          const visualStatus = getAgentStatus(step.key, currentStage);

          return (
            <article
              key={step.key}
              className={[
                "relative rounded-2xl border p-4 transition-all duration-300",
                statusClasses[visualStatus],
              ].join(" ")}
            >
              {visualStatus === "complete" ? (
                <CheckCircle2 className="absolute right-3 top-3 h-5 w-5" />
              ) : null}
              <div className="flex items-start gap-3">
                <div className="rounded-2xl bg-white/70 p-3 shadow-sm dark:bg-slate-900/80">
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="font-semibold">{step.label}</p>
                  <p
                    className="mt-1 text-xs uppercase tracking-[0.22em]"
                    data-testid={`agent-${step.label.toLowerCase()}-status`}
                  >
                    {visualStatus}
                  </p>
                </div>
              </div>
            </article>
          );
        })}
      </div>

      <div className="mt-6">
        <div className="mb-2 flex items-center justify-between text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">
          <span>Progress</span>
          <span>{clampedProgress}%</span>
        </div>
        <progress
          aria-label="Report progress"
          className="h-3 w-full overflow-hidden rounded-full [appearance:none] [&::-moz-progress-bar]:rounded-full [&::-moz-progress-bar]:bg-brand-ocean dark:[&::-moz-progress-bar]:bg-brand-gold [&::-webkit-progress-bar]:rounded-full [&::-webkit-progress-bar]:bg-slate-200 dark:[&::-webkit-progress-bar]:bg-slate-800 [&::-webkit-progress-value]:rounded-full [&::-webkit-progress-value]:bg-brand-ocean dark:[&::-webkit-progress-value]:bg-brand-gold"
          max={100}
          value={clampedProgress}
        />
      </div>
    </section>
  );
};
