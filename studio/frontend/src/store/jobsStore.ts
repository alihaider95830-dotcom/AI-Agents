"use client";

import { toast } from "sonner";
import { create } from "zustand";

import { extractApiErrorMessage, jobsApi } from "@/lib/api";
import type { FinalReport, JobStatus } from "@/types/jobs";

interface JobsStoreState {
  currentJobId: string | null;
  currentReportId: string | null;
  jobStatus: JobStatus | null;
  finalReport: FinalReport | null;
  pollingInterval: number | null;
  setJob: (job_id: string) => void;
  setJobStatus: (status: JobStatus) => void;
  setFinalReport: (report: FinalReport) => void;
  startPolling: (
    job_id: string,
    token: string,
    intervalMs?: number,
  ) => Promise<void>;
  stopPolling: () => void;
  reset: () => void;
}

export const useJobsStore = create<JobsStoreState>((set, get) => ({
  currentJobId: null,
  currentReportId: null,
  jobStatus: null,
  finalReport: null,
  pollingInterval: null,
  setJob: (job_id) => {
    get().stopPolling();
    set({
      currentJobId: job_id,
      currentReportId: null,
      jobStatus: null,
      finalReport: null,
    });
  },
  setJobStatus: (status) => {
    set({ jobStatus: status });
  },
  setFinalReport: (report) => {
    set({
      finalReport: report,
      currentReportId: report.report_id ?? get().currentReportId,
    });
  },
  startPolling: async (job_id, token, intervalMs = 5000) => {
    void token;
    get().stopPolling();
    let shouldContinuePolling = true;

    const pollStatus = async (): Promise<void> => {
      try {
        const status = await jobsApi.getStatus(job_id);
        get().setJobStatus(status);

        if (status.status === "complete" || status.status === "failed") {
          shouldContinuePolling = false;
          get().stopPolling();
        }
      } catch (error) {
        shouldContinuePolling = false;
        toast.error(extractApiErrorMessage(error));
        get().stopPolling();
      }
    };

    await pollStatus();

    if (!shouldContinuePolling) {
      return;
    }

    const intervalHandle = window.setInterval(() => {
      void pollStatus();
    }, intervalMs);

    set({ pollingInterval: intervalHandle });
  },
  stopPolling: () => {
    const intervalHandle = get().pollingInterval;
    if (intervalHandle) {
      window.clearInterval(intervalHandle);
    }

    set({ pollingInterval: null });
  },
  reset: () => {
    get().stopPolling();
    set({
      currentJobId: null,
      currentReportId: null,
      jobStatus: null,
      finalReport: null,
      pollingInterval: null,
    });
  },
}));
