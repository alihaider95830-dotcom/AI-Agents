import type { ReportStatus } from "@/lib/api/reports";
import { cn } from "@/lib/utils";

const statusClasses: Record<ReportStatus, string> = {
  pending:
    "bg-slate-100 text-slate-700 ring-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:ring-slate-700",
  running:
    "animate-pulse bg-blue-100 text-blue-700 ring-blue-200 dark:bg-blue-950 dark:text-blue-200 dark:ring-blue-800",
  done:
    "bg-emerald-100 text-emerald-700 ring-emerald-200 dark:bg-emerald-950 dark:text-emerald-200 dark:ring-emerald-800",
  failed:
    "bg-red-100 text-red-700 ring-red-200 dark:bg-red-950 dark:text-red-200 dark:ring-red-800",
};

const statusLabels: Record<ReportStatus, string> = {
  pending: "Pending",
  running: "Generating...",
  done: "Done",
  failed: "Failed",
};

interface ReportStatusBadgeProps {
  status: ReportStatus;
  className?: string;
}

export const ReportStatusBadge = ({
  className,
  status,
}: ReportStatusBadgeProps): JSX.Element => (
  <span
    className={cn(
      "inline-flex w-fit items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1",
      statusClasses[status],
      className,
    )}
  >
    {statusLabels[status]}
  </span>
);
