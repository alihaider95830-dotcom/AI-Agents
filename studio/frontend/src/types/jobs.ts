export type JobLifecycleStatus =
  | "queued"
  | "researching"
  | "planning"
  | "writing"
  | "qa"
  | "complete"
  | "failed";

export type ReportType =
  | "analytical"
  | "informational"
  | "comparative"
  | "argumentative";

export interface JobStatus {
  job_id: string;
  status: JobLifecycleStatus;
  agent_stage: string;
  progress_pct: number;
  error?: string;
}

export interface Citation {
  index: number;
  url: string;
  title: string;
  inline_reference: string;
}

export interface FinalReport {
  topic: string;
  report_type: string;
  executive_summary: string;
  markdown_output: string;
  total_word_count: number;
  quality_score: number;
  qa_passed: boolean;
  all_citations: Citation[];
  timestamp: string;
  report_id?: string;
}

export const REPORT_TYPE_OPTIONS: Array<{
  label: string;
  value: ReportType;
}> = [
  { label: "Analytical", value: "analytical" },
  { label: "Informational", value: "informational" },
  { label: "Comparative", value: "comparative" },
  { label: "Argumentative", value: "argumentative" },
];
