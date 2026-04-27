import { apiRequest } from "@/lib/api/client";
import type { ReportStatus } from "@/lib/api/reports";

export interface JobStatusResponse {
  job_id: string;
  report_id: string;
  status: ReportStatus;
  current_agent: string | null;
  progress_pct: number;
  error_message: string | null;
  created_at: string;
}

export const getJob = async (
  token: string,
  jobId: string,
): Promise<JobStatusResponse> => apiRequest<JobStatusResponse>(`/jobs/${jobId}`, token);
