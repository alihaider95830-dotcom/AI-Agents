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
    "border-white/05 bg-white/02 text-[var(--text-tertiary)] opacity-50",
  active:
    "border-white/20 bg-white/08 text-white animate-pulse shadow-[0_0_20px_rgba(255,255,255,0.05)]",
  complete:
    "border-white/10 bg-white/05 text-[var(--text-secondary)]",
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
    <section className="glass-card p-8 bg-white/[0.02] border-white/[0.05] relative overflow-hidden glass-scanline">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between relative z-10">
        <div>
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/05 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.15em] text-[var(--text-secondary)] backdrop-blur-md">
            <span className="h-1 w-1 rounded-full bg-white animate-pulse shadow-[0_0_8px_white]" />
            LIVE_CREW_STREAM
          </span>
          <h2 className="mt-6 text-[22px] font-semibold tracking-tight text-white">
            Operational Intelligence
          </h2>
        </div>
        <p className="text-[13px] font-bold font-mono text-[var(--text-tertiary)] uppercase tracking-widest opacity-60">
          PROG_STATUS: <span className="text-white">{clampedProgress}%</span>
        </p>
      </div>

      <div className="mt-10 grid gap-4 md:grid-cols-4 relative z-10">
        {agentSteps.map((step) => {
          const Icon = step.icon;
          const visualStatus = getAgentStatus(step.key, currentStage);

          return (
            <article
              key={step.key}
              className={[
                "relative flex flex-col gap-4 rounded-[var(--radius-lg)] border p-6 transition-all duration-700",
                statusClasses[visualStatus],
                visualStatus === 'active' ? 'border-white/30 !bg-white/[0.08] shadow-[0_0_30px_rgba(255,255,255,0.05)]' : 'border-white/05'
              ].join(" ")}
            >
              <div className="flex items-center justify-between">
                <div className={["rounded-[var(--radius-md)] p-2.5 transition-colors duration-500", visualStatus === 'active' ? 'bg-white text-black' : 'bg-white/05 text-[var(--text-tertiary)]'].join(" ")}>
                  <Icon className="h-4 w-4" />
                </div>
                {visualStatus === "complete" ? (
                  <div className="h-6 w-6 rounded-full bg-white/10 flex items-center justify-center">
                    <CheckCircle2 className="h-3.5 w-3.5 text-white/60" />
                  </div>
                ) : visualStatus === "active" ? (
                  <span className="flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-white opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
                  </span>
                ) : null}
              </div>
              <div>
                <p className={["text-[14px] font-bold tracking-tight transition-colors duration-500", visualStatus === 'active' ? 'text-white' : 'text-[var(--text-secondary)]'].join(" ")}>{step.label}</p>
                <p
                  data-testid={`agent-${step.key}-status`}
                  className="mt-1 text-[9px] font-bold uppercase tracking-[0.2em] opacity-40 font-mono"
                >
                  [{visualStatus}]
                </p>
              </div>
            </article>
          );
        })}
      </div>

      <div className="mt-12 relative z-10">
        <div className="mb-4 flex items-center justify-between text-[10px] font-bold uppercase tracking-[0.25em] text-[var(--text-tertiary)] font-mono">
          <span>PIPELINE_STABILITY</span>
          <span className="text-white opacity-60">ACTIVE_FLOW</span>
        </div>
        <div className="h-1 w-full overflow-hidden rounded-full bg-white/05">
          <div 
            className="h-full bg-white transition-all duration-1000 ease-[var(--ease-out)] shadow-[0_0_20px_rgba(255,255,255,0.5)]" 
            style={{ width: `${clampedProgress}%` }}
          />
        </div>
      </div>
    </section>
  );
};
