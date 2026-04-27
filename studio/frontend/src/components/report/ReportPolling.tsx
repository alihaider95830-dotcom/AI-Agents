"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useSupabaseAccessToken } from "@/hooks/useSupabaseAccessToken";
import { getJob, type JobStatusResponse } from "@/lib/api/jobs";
import type { ReportStatus } from "@/lib/api/reports";
import { cn } from "@/lib/utils";

interface ReportPollingProps {
  reportId: string;
  jobId: string;
  initialStatus: ReportStatus;
}

const agentSteps = ["researcher", "planner", "writer", "qa"] as const;

const agentLabels: Record<(typeof agentSteps)[number], string> = {
  researcher: "Researcher",
  planner: "Planner",
  writer: "Writer",
  qa: "QA",
};

const normalizeAgent = (
  agent: string | null | undefined,
): (typeof agentSteps)[number] => {
  const cleanedAgent = (agent ?? "researcher").toLowerCase();
  if (cleanedAgent.includes("planner")) {
    return "planner";
  }
  if (cleanedAgent.includes("writer")) {
    return "writer";
  }
  if (cleanedAgent.includes("qa")) {
    return "qa";
  }
  return "researcher";
};

export const ReportPolling = ({
  jobId,
  initialStatus,
}: ReportPollingProps): JSX.Element | null => {
  const router = useRouter();
  const { token } = useSupabaseAccessToken();
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isStopped, setIsStopped] = useState(false);
  const currentAgent = normalizeAgent(job?.current_agent);
  const currentIndex = agentSteps.indexOf(currentAgent);
  const progress = Math.max(0, Math.min(job?.progress_pct ?? 0, 100));

  const statusLabel = useMemo(() => {
    if (error) {
      return error;
    }
    if (!job) {
      return "Preparing report job...";
    }
    return `${agentLabels[currentAgent]} is working`;
  }, [currentAgent, error, job]);

  useEffect(() => {
    if (initialStatus === "done" || initialStatus === "failed") {
      return;
    }
    if (!token || isStopped) {
      return;
    }

    let isMounted = true;
    let intervalId: number | null = null;

    const poll = async (): Promise<void> => {
      try {
        const nextJob = await getJob(token, jobId);
        if (!isMounted) {
          return;
        }

        setJob(nextJob);
        setError(null);

        if (nextJob.status === "done") {
          setIsStopped(true);
          if (intervalId) {
            window.clearInterval(intervalId);
          }
          router.refresh();
        }

        if (nextJob.status === "failed") {
          setIsStopped(true);
          if (intervalId) {
            window.clearInterval(intervalId);
          }
          setError(nextJob.error_message ?? "Report generation failed.");
        }
      } catch (pollError) {
        if (!isMounted) {
          return;
        }
        setIsStopped(true);
        setError(
          pollError instanceof Error
            ? pollError.message
            : "Unable to refresh job status.",
        );
      }
    };

    void poll();
    intervalId = window.setInterval(() => {
      void poll();
    }, 3000);

    return () => {
      isMounted = false;
      if (intervalId) {
        window.clearInterval(intervalId);
      }
    };
  }, [initialStatus, isStopped, jobId, router, token]);

  if (initialStatus === "done" || initialStatus === "failed") {
    return null;
  }

  return (
    <section className="mx-auto mt-6 max-w-6xl px-4 sm:px-6 lg:px-8">
      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-medium text-slate-950 dark:text-slate-50">
              {statusLabel}
            </p>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Job {jobId}
            </p>
          </div>
          <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">
            {progress}%
          </p>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-4">
          {agentSteps.map((agent, index) => {
            const isFilled = progress >= 100 || index < currentIndex;
            const isActive = index === currentIndex && !error;

            return (
              <div
                className="flex items-center gap-2 text-sm"
                key={agent}
              >
                <span
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full border text-xs font-semibold",
                    isFilled &&
                      "border-emerald-500 bg-emerald-500 text-white",
                    isActive &&
                      "animate-pulse border-blue-500 bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-200",
                    !isFilled &&
                      !isActive &&
                      "border-slate-200 bg-slate-100 text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400",
                  )}
                >
                  {index + 1}
                </span>
                <span className="font-medium text-slate-700 dark:text-slate-200">
                  {agentLabels[agent]}
                </span>
              </div>
            );
          })}
        </div>

        <div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-900">
          <div
            className="h-full rounded-full bg-blue-600 transition-all duration-500 dark:bg-blue-400"
            style={{ width: `${progress}%` }}
          />
        </div>

        {error ? (
          <p className="mt-4 text-sm font-medium text-red-600 dark:text-red-300">
            {error}
          </p>
        ) : null}
      </div>
    </section>
  );
};
