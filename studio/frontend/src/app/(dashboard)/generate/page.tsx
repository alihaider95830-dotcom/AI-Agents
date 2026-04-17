"use client";

import Link from "next/link";
import { useEffect, useReducer } from "react";
import { LoaderCircle, RefreshCw } from "lucide-react";
import { toast } from "sonner";

import { AgentStatusBar } from "@/components/generate/AgentStatusBar";
import { StreamViewer } from "@/components/generate/StreamViewer";
import { TopicForm } from "@/components/generate/TopicForm";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useSSEStream } from "@/hooks/useSSEStream";
import { useSession } from "@/hooks/useSession";
import { extractApiErrorMessage, jobsApi, reportsApi } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { useJobsStore } from "@/store/jobsStore";
import { REPORT_TYPE_OPTIONS, type ReportType } from "@/types/jobs";

type GenerateMode = "idle" | "queued" | "streaming" | "complete" | "failed";

interface GeneratePageState {
  mode: GenerateMode;
  error: string | null;
  creditsDeducted: number;
  creditRefunded: boolean;
  isSubmitting: boolean;
}

type GeneratePageAction =
  | {
      type: "SUBMIT_STARTED";
    }
  | {
      type: "QUEUE_JOB";
      payload: {
        creditsDeducted: number;
      };
    }
  | { type: "START_STREAMING" }
  | { type: "COMPLETE" }
  | { type: "FAIL"; payload: { error: string } }
  | { type: "MARK_REFUND_APPLIED" }
  | { type: "RESET" };

const initialState: GeneratePageState = {
  mode: "idle",
  error: null,
  creditsDeducted: 0,
  creditRefunded: false,
  isSubmitting: false,
};

const generatePageReducer = (
  state: GeneratePageState,
  action: GeneratePageAction,
): GeneratePageState => {
  switch (action.type) {
    case "SUBMIT_STARTED":
      return {
        ...state,
        isSubmitting: true,
        error: null,
      };
    case "QUEUE_JOB":
      return {
        mode: "queued",
        error: null,
        creditsDeducted: action.payload.creditsDeducted,
        creditRefunded: false,
        isSubmitting: false,
      };
    case "START_STREAMING":
      return {
        ...state,
        mode: "streaming",
        isSubmitting: false,
      };
    case "COMPLETE":
      return {
        ...state,
        mode: "complete",
        error: null,
        isSubmitting: false,
      };
    case "FAIL":
      return {
        ...state,
        mode: "failed",
        error: action.payload.error,
        isSubmitting: false,
      };
    case "MARK_REFUND_APPLIED":
      return {
        ...state,
        creditRefunded: true,
      };
    case "RESET":
      return initialState;
    default:
      return state;
  }
};

const formatTimestamp = (timestamp: string): string => {
  const parsedDate = new Date(timestamp);

  if (Number.isNaN(parsedDate.getTime())) {
    return timestamp;
  }

  return parsedDate.toLocaleString();
};

export default function GeneratePage(): JSX.Element {
  const [{ mode, error, creditsDeducted, creditRefunded, isSubmitting }, dispatch] =
    useReducer(generatePageReducer, initialState);
  const { user, token } = useSession();
  const adjustCredits = useAuthStore((state) => state.adjustCredits);
  const currentJobId = useJobsStore((state) => state.currentJobId);
  const currentReportId = useJobsStore((state) => state.currentReportId);
  const jobStatus = useJobsStore((state) => state.jobStatus);
  const finalReport = useJobsStore((state) => state.finalReport);
  const setJob = useJobsStore((state) => state.setJob);
  const setJobStatus = useJobsStore((state) => state.setJobStatus);
  const setFinalReport = useJobsStore((state) => state.setFinalReport);
  const startPolling = useJobsStore((state) => state.startPolling);
  const stopPolling = useJobsStore((state) => state.stopPolling);
  const resetJobs = useJobsStore((state) => state.reset);
  const sseStream = useSSEStream(mode === "streaming" ? currentJobId : null, token);

  const displayedMarkdown =
    finalReport?.markdown_output ?? sseStream.streamedText;
  const effectiveStage =
    mode === "complete"
      ? "complete"
      : sseStream.currentStage !== "queued"
        ? sseStream.currentStage
        : jobStatus?.status ?? "queued";
  const progress = mode === "complete" ? 100 : jobStatus?.progress_pct ?? 0;

  useEffect(() => {
    return () => {
      stopPolling();
      resetJobs();
    };
  }, [resetJobs, stopPolling]);

  useEffect(() => {
    if (!jobStatus) {
      return;
    }

    if (jobStatus.status === "failed" && mode !== "failed") {
      stopPolling();
      const errorMessage = jobStatus.error ?? "The report job failed.";
      toast.error(errorMessage);
      dispatch({
        type: "FAIL",
        payload: { error: errorMessage },
      });
      return;
    }

    if (
      mode === "queued" &&
      jobStatus.status !== "queued" &&
      jobStatus.status !== "failed"
    ) {
      dispatch({ type: "START_STREAMING" });

      if (currentJobId && token) {
        void startPolling(currentJobId, token, 5000);
      }
    }
  }, [currentJobId, jobStatus, mode, startPolling, stopPolling, token]);

  useEffect(() => {
    if (mode !== "streaming" || !sseStream.error) {
      return;
    }

    stopPolling();
    toast.error(sseStream.error);
    dispatch({
      type: "FAIL",
      payload: { error: sseStream.error },
    });
  }, [mode, sseStream.error, stopPolling]);

  useEffect(() => {
    const completedReportId = sseStream.reportId;

    if (
      mode !== "streaming" ||
      !sseStream.isComplete ||
      !completedReportId ||
      currentReportId === completedReportId
    ) {
      return;
    }

    stopPolling();

    const loadFinalReport = async (): Promise<void> => {
      try {
        const report = await reportsApi.get(completedReportId);
        setFinalReport({
          ...report,
          report_id: completedReportId,
        });
        dispatch({ type: "COMPLETE" });
      } catch (loadError) {
        toast.error(extractApiErrorMessage(loadError));
        dispatch({
          type: "FAIL",
          payload: {
            error: "The report finished, but the final result could not be loaded.",
          },
        });
      }
    };

    void loadFinalReport();
  }, [
    currentReportId,
    mode,
    sseStream.reportId,
    setFinalReport,
    sseStream.isComplete,
    stopPolling,
  ]);

  useEffect(() => {
    if (mode !== "failed" || creditsDeducted <= 0 || creditRefunded) {
      return;
    }

    adjustCredits(creditsDeducted);
    dispatch({ type: "MARK_REFUND_APPLIED" });
  }, [adjustCredits, creditRefunded, creditsDeducted, mode]);

  const handleCreateJob = async (
    topic: string,
    report_type: ReportType,
  ): Promise<void> => {
    try {
      dispatch({ type: "SUBMIT_STARTED" });
      const response = await jobsApi.create(topic, report_type);
      setJob(response.job_id);
      setJobStatus({
        job_id: response.job_id,
        status: "queued",
        agent_stage: "queued",
        progress_pct: 0,
      });
      adjustCredits(response.credits_deducted * -1);
      dispatch({
        type: "QUEUE_JOB",
        payload: {
          creditsDeducted: response.credits_deducted,
        },
      });

      if (token) {
        await startPolling(response.job_id, token, 3000);
      }
    } catch (submitError) {
      toast.error(extractApiErrorMessage(submitError));
      dispatch({ type: "RESET" });
    }
  };

  const handleReset = (): void => {
    stopPolling();
    resetJobs();
    dispatch({ type: "RESET" });
  };

  const handleCopyMarkdown = async (): Promise<void> => {
    if (!finalReport) {
      return;
    }

    try {
      await navigator.clipboard.writeText(finalReport.markdown_output);
      toast.success("Markdown copied to your clipboard.");
    } catch {
      toast.error("Unable to copy the markdown right now.");
    }
  };

  const downloadPdfHref = finalReport?.report_id
    ? `/api/reports/${finalReport.report_id}/pdf`
    : "#";

  return (
    <div className="space-y-6">
      {(mode === "idle" || mode === "queued") && user ? (
        <section className="rounded-[1.5rem] border border-brand-mist bg-brand-mist/80 px-5 py-4 text-sm text-brand-ink shadow-sm dark:border-slate-800 dark:bg-slate-900/70 dark:text-slate-100">
          You have {user.credits} credits remaining. Each report costs 1 credit.
        </section>
      ) : null}

      {mode === "idle" ? (
        <TopicForm
          creditsRemaining={user?.credits ?? 0}
          isLoading={isSubmitting}
          onSubmit={handleCreateJob}
        />
      ) : null}

      {mode === "queued" ? (
        <section className="rounded-[1.75rem] border border-slate-200/70 bg-white/85 p-6 shadow-panel dark:border-slate-800 dark:bg-slate-950/80">
          <div className="flex items-center gap-3 text-slate-700 dark:text-slate-200">
            <LoaderCircle className="h-5 w-5 animate-spin text-brand-ocean dark:text-brand-gold" />
            <div>
              <h2 className="font-[var(--font-heading)] text-2xl font-semibold text-slate-900 dark:text-white">
                Job queued...
              </h2>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                We&apos;ve handed your topic to the crew and are waiting for the
                first agent to begin.
              </p>
            </div>
          </div>
        </section>
      ) : null}

      {mode === "streaming" || mode === "complete" ? (
        <div className="space-y-6 transition-all duration-300">
          <AgentStatusBar
            currentStage={effectiveStage}
            progress_pct={progress}
          />
          <StreamViewer
            isComplete={mode === "complete"}
            isStreaming={mode === "streaming" && sseStream.isStreaming}
            streamedText={displayedMarkdown}
          />

          {mode === "complete" && finalReport && finalReport.report_id ? (
            <section className="rounded-[1.75rem] border border-slate-200/70 bg-white/85 p-6 shadow-panel dark:border-slate-800 dark:bg-slate-950/80">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.35em] text-brand-ocean dark:text-brand-gold">
                    Delivery
                  </p>
                  <h3 className="mt-2 font-[var(--font-heading)] text-2xl font-semibold text-slate-900 dark:text-white">
                    Final report is ready
                  </h3>
                </div>
                <div className="flex flex-col gap-3 sm:flex-row">
                  <Link
                    className="inline-flex h-11 items-center justify-center rounded-xl bg-brand-mist px-4 text-sm font-medium text-brand-ink transition-all duration-200 hover:bg-sky-100 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
                    href={downloadPdfHref}
                  >
                    Download PDF
                  </Link>
                  <Button
                    className="sm:w-auto"
                    onClick={() => {
                      void handleCopyMarkdown();
                    }}
                    variant="secondary"
                  >
                    Copy Markdown
                  </Button>
                  <Button
                    className="sm:w-auto"
                    onClick={handleReset}
                    variant="ghost"
                  >
                    New Report
                  </Button>
                </div>
              </div>

              <div className="mt-6 flex flex-wrap gap-3">
                <Badge>{finalReport.total_word_count} words</Badge>
                <Badge>{Math.round(finalReport.quality_score * 100)}% quality</Badge>
                <Badge>{formatTimestamp(finalReport.timestamp)}</Badge>
              </div>
            </section>
          ) : null}
        </div>
      ) : null}

      {mode === "failed" ? (
        <section className="rounded-[1.75rem] border border-rose-200 bg-rose-50/80 p-6 shadow-panel dark:border-rose-900/60 dark:bg-rose-950/20">
          <p className="text-xs uppercase tracking-[0.35em] text-rose-500">
            Job failed
          </p>
          <h2 className="mt-2 font-[var(--font-heading)] text-2xl font-semibold text-slate-900 dark:text-white">
            We hit a snag while generating your report
          </h2>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
            {error}
          </p>
          <Button
            className="mt-6"
            onClick={handleReset}
            variant="secondary"
          >
            <RefreshCw className="h-4 w-4" />
            Try Again
          </Button>
        </section>
      ) : null}

      {mode === "idle" ? (
        <section className="rounded-[1.75rem] border border-slate-200/70 bg-white/75 p-6 shadow-panel dark:border-slate-800 dark:bg-slate-950/75">
          <p className="text-xs uppercase tracking-[0.35em] text-brand-ocean dark:text-brand-gold">
            Report modes
          </p>
          <div className="mt-4 grid gap-4 lg:grid-cols-4">
            {REPORT_TYPE_OPTIONS.map((option) => (
              <article
                key={option.value}
                className="rounded-2xl border border-slate-200/70 bg-white/80 p-4 dark:border-slate-800 dark:bg-slate-900/70"
              >
                <h3 className="font-semibold capitalize text-slate-900 dark:text-white">
                  {option.label}
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
                  Shape the report structure around a {option.value} lens with
                  an end-to-end AI crew workflow.
                </p>
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
