import type { ReportStatus, ReportType } from "@/lib/api/reports";

const reportDateFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  year: "numeric",
});

export const truncateText = (value: string, maxLength: number): string => {
  if (value.length <= maxLength) {
    return value;
  }

  return `${value.slice(0, Math.max(maxLength - 3, 1)).trimEnd()}...`;
};

export const formatReportDate = (value: string | null): string => {
  if (!value) {
    return "—";
  }

  const parsedDate = new Date(value);
  if (Number.isNaN(parsedDate.getTime())) {
    return "—";
  }

  return reportDateFormatter.format(parsedDate);
};

export const formatReportType = (reportType: ReportType): string =>
  reportType
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");

export const reportStatusLabels: Record<ReportStatus, string> = {
  pending: "Pending",
  running: "Generating...",
  done: "Done",
  failed: "Failed",
};
