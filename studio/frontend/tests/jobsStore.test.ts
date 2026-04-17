import { toast } from "sonner";

import { jobsApi } from "@/lib/api";
import { useJobsStore } from "@/store/jobsStore";
import type { FinalReport, JobStatus } from "@/types/jobs";

jest.mock("sonner", () => ({
  toast: {
    error: jest.fn(),
  },
}));

const mockedToast = toast as jest.Mocked<typeof toast>;

const jobStatus: JobStatus = {
  job_id: "job-1",
  status: "writing",
  agent_stage: "writing",
  progress_pct: 65,
};

const report: FinalReport = {
  topic: "Test topic",
  report_type: "analytical",
  executive_summary: "Summary",
  markdown_output: "# Title",
  total_word_count: 400,
  quality_score: 0.88,
  qa_passed: true,
  all_citations: [],
  timestamp: "2026-04-17T12:00:00.000Z",
  report_id: "report-1",
};

describe("jobsStore", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useJobsStore.getState().reset();
  });

  afterEach(() => {
    useJobsStore.getState().reset();
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  it("test_set_job_clears_previous", () => {
    useJobsStore.setState({
      currentJobId: "job-old",
      currentReportId: "report-old",
      jobStatus,
      finalReport: report,
    });

    useJobsStore.getState().setJob("job-new");
    useJobsStore.getState().setJob("job-latest");

    expect(useJobsStore.getState().currentJobId).toBe("job-latest");
    expect(useJobsStore.getState().currentReportId).toBeNull();
    expect(useJobsStore.getState().jobStatus).toBeNull();
    expect(useJobsStore.getState().finalReport).toBeNull();
  });

  it("test_polling_updates_status", async () => {
    jest.useFakeTimers();
    jest.spyOn(jobsApi, "getStatus").mockResolvedValue(jobStatus);

    await useJobsStore.getState().startPolling("job-1", "token-123", 1000);

    expect(jobsApi.getStatus).toHaveBeenCalledWith("job-1");
    expect(useJobsStore.getState().jobStatus).toEqual(jobStatus);
    expect(useJobsStore.getState().pollingInterval).not.toBeNull();
  });

  it("test_reset_clears_all", () => {
    useJobsStore.setState({
      currentJobId: "job-1",
      currentReportId: "report-1",
      jobStatus,
      finalReport: report,
      pollingInterval: window.setInterval(() => undefined, 1000),
    });

    useJobsStore.getState().reset();

    expect(useJobsStore.getState().currentJobId).toBeNull();
    expect(useJobsStore.getState().currentReportId).toBeNull();
    expect(useJobsStore.getState().jobStatus).toBeNull();
    expect(useJobsStore.getState().finalReport).toBeNull();
    expect(useJobsStore.getState().pollingInterval).toBeNull();
    expect(mockedToast.error).not.toHaveBeenCalled();
  });
});
