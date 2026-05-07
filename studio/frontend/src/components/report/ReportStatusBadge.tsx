import type { ReportStatus } from "@/lib/api/reports";
import { cn } from "@/lib/utils";

const statusClasses: Record<ReportStatus, string> = {
  pending:
    "bg-white/05 text-[var(--text-tertiary)] border-white/10",
  running:
    "animate-pulse bg-[var(--status-info)] text-[var(--status-info-text)] border-[var(--status-info-text)]/20",
  done:
    "bg-[var(--status-success)] text-[var(--status-success-text)] border-[var(--status-success-text)]/20",
  failed:
    "bg-[var(--status-error)] text-[var(--status-error-text)] border-[var(--status-error-text)]/20",
};

const statusLabels: Record<ReportStatus, string> = {
  pending: "Pending",
  running: "Generating",
  done: "Ready",
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
      "inline-flex w-fit items-center rounded-full border px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-[0.06em] backdrop-blur-sm",
      statusClasses[status],
      className,
    )}
  >
    {statusLabels[status]}
  </span>
);
