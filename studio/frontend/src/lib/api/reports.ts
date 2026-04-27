import { apiRequest, buildApiUrl, type ApiError } from "@/lib/api/client";

export type ReportStatus = "pending" | "running" | "done" | "failed";

export type ReportType =
  | "market_analysis"
  | "competitor_overview"
  | "trend_report"
  | "industry_deep_dive";

export interface Report {
  id: string;
  title: string;
  topic: string;
  report_type: ReportType;
  status: ReportStatus;
  content_md: string | null;
  word_count: number | null;
  created_at: string;
  completed_at: string | null;
  job_id?: string | null;
}

export interface PaginatedReports {
  items: Report[];
  total: number;
  page: number;
  page_size: number;
}

export const getReports = async (
  token: string,
  page = 1,
  pageSize = 10,
): Promise<PaginatedReports> =>
  apiRequest<PaginatedReports>(
    `/reports?page=${page}&page_size=${pageSize}`,
    token,
  );

export const getReport = async (
  token: string,
  reportId: string,
): Promise<Report> =>
  apiRequest<Report>(`/reports/${reportId}`, token);

export const deleteReport = async (
  token: string,
  reportId: string,
): Promise<void> => {
  await apiRequest<void>(`/reports/${reportId}`, token, {
    method: "DELETE",
  });
};

export const getPdfUrl = (reportId: string): string =>
  buildApiUrl(`/reports/${reportId}/export/pdf`);

export type { ApiError };
