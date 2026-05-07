"use client";

import Link from "next/link";
import { useEffect, useReducer } from "react";
import { LoaderCircle, RefreshCw, FileText, Download, Copy, Plus } from "lucide-react";
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
    <div className="space-y-10 max-w-5xl mx-auto">
      {(mode === "idle" || mode === "queued") && user ? (
        <section className="glass-card !bg-white/[0.02] px-5 py-3 text-[13px] text-[var(--text-secondary)]">
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-white/20" />
            <span>You have {user.credits} credits remaining. Each report costs 1 credit.</span>
          </div>
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
        <section className="glass-elevated p-10 text-center animate-glass-enter">
          <div className="flex flex-col items-center gap-6">
            <div className="relative">
              <div className="absolute inset-0 blur-2xl bg-white/10 rounded-full animate-pulse" />
              <LoaderCircle className="h-12 w-12 animate-spin text-white relative z-10" />
            </div>
            <div>
              <h2 className="text-[26px] font-semibold text-[var(--text-primary)] tracking-tight">
                Job queued...
              </h2>
              <p className="mt-2 text-[15px] text-[var(--text-secondary)] max-w-md mx-auto leading-relaxed">
                We&apos;ve handed your topic to the crew and are waiting for the
                first agent to begin.
              </p>
            </div>
          </div>
        </section>
      ) : null}

      {mode === "streaming" || mode === "complete" ? (
        <div className="space-y-8 animate-glass-enter">
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
            <section className="glass-elevated p-8 bg-white/[0.04]">
              <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <p className="text-[10px] uppercase tracking-[0.3em] text-[var(--text-tertiary)]">
                    DELIVERY
                  </p>
                  <h3 className="mt-1 text-[20px] font-semibold text-[var(--text-primary)]">
                    Final report is ready
                  </h3>
                </div>
                <div className="flex flex-wrap gap-3">
                  <Link href={downloadPdfHref} passHref legacyBehavior>
                    <Button variant="primary">
                      <Download className="h-4 w-4 mr-2" />
                      Download PDF
                    </Button>
                  </Link>
                  <Button
                    onClick={() => {
                      void handleCopyMarkdown();
                    }}
                    variant="secondary"
                  >
                    <Copy className="h-4 w-4 mr-2" />
                    Copy Markdown
                  </Button>
                  <Button
                    onClick={handleReset}
                    variant="ghost"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    New Report
                  </Button>
                </div>
              </div>

              <div className="mt-8 flex flex-wrap gap-4 pt-6 border-t border-white/05">
                <Badge variant="default">{finalReport.total_word_count} words</Badge>
                <Badge variant="pro">{Math.round(finalReport.quality_score * 100)}% quality</Badge>
                <Badge variant="default" className="font-mono">{formatTimestamp(finalReport.timestamp)}</Badge>
              </div>
            </section>
          ) : null}
        </div>
      ) : null}

      {mode === "failed" ? (
        <section className="glass-elevated p-10 border-red-500/20 bg-red-500/[0.02] animate-glass-enter">
          <p className="text-[10px] uppercase tracking-[0.35em] text-red-400">
            Job failed
          </p>
          <h2 className="mt-2 text-[26px] font-semibold text-[var(--text-primary)]">
            We hit a snag while generating your report
          </h2>
          <p className="mt-4 max-w-2xl text-[15px] leading-7 text-[var(--text-secondary)]">
            {error}
          </p>
          <Button
            className="mt-8"
            onClick={handleReset}
            variant="secondary"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
        </section>
      ) : null}

      {mode === "idle" ? (
        <section className="animate-glass-enter">
          <div className="flex items-center gap-3 mb-6">
            <span className="h-px flex-1 bg-white/05" />
            <p className="text-[10px] uppercase tracking-[0.35em] text-[var(--text-tertiary)] font-medium">
              Report modes
            </p>
            <span className="h-px flex-1 bg-white/05" />
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {REPORT_TYPE_OPTIONS.map((option) => (
              <article
                key={option.value}
                className="glass-card p-6 !bg-white/[0.02] group hover:!bg-white/[0.05]"
              >
                <h3 className="text-[15px] font-semibold capitalize text-[var(--text-primary)] group-hover:text-white transition-colors">
                  {option.label}
                </h3>
                <p className="mt-3 text-[13px] leading-6 text-[var(--text-secondary)]">
                  Shape the report structure around a <span className="text-[var(--text-tertiary)]">{option.value}</span> lens with
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
