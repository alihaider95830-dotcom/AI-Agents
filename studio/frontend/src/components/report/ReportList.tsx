"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Eye, FileText, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { ReportStatusBadge } from "@/components/report/ReportStatusBadge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/Button";
import { useSupabaseAccessToken } from "@/hooks/useSupabaseAccessToken";
import {
  deleteReport,
  getReports,
  type PaginatedReports,
  type Report,
} from "@/lib/api/reports";
import {
  formatReportDate,
  formatReportType,
  truncateText,
} from "@/lib/report-helpers";

interface ReportListProps {
  initialData: PaginatedReports;
}

const ReportCardSkeleton = (): JSX.Element => (
  <div
    className="glass-card h-36 animate-pulse p-6 border-white/05"
    data-testid="report-card-skeleton"
  >
    <div className="h-4 w-1/3 rounded bg-white/05" />
    <div className="mt-4 h-3 w-3/4 rounded bg-white/05" />
    <div className="mt-8 h-8 w-full rounded bg-white/05" />
  </div>
);

const ReportCard = ({
  onDeleted,
  report,
}: {
  onDeleted: (reportId: string) => void;
  report: Report;
}): JSX.Element => {
  const { token } = useSupabaseAccessToken();
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async (): Promise<void> => {
    if (!token) {
      toast.error("Your session is not ready yet.");
      return;
    }

    try {
      setIsDeleting(true);
      await deleteReport(token, report.id);
      onDeleted(report.id);
      toast.success("Report deleted.");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to delete report.";
      toast.error(message);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <article className="glass-card p-6 border-white/05 relative overflow-hidden glass-scanline group">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between relative z-10">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="text-[17px] font-bold tracking-tight text-white group-hover:text-white/90 transition-colors">
              {report.title}
            </h2>
            <ReportStatusBadge status={report.status} />
          </div>
          <p className="mt-2 text-[14px] leading-relaxed text-[var(--text-secondary)] opacity-80">
            {truncateText(report.topic, 120)}
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <Link href={`/reports/${report.id}`} passHref legacyBehavior>
            <Button
              aria-label={`View ${report.title}`}
              size="sm"
              variant="secondary"
              className="!rounded-full !bg-white/05 hover:!bg-white/10 btn-glow"
            >
              <Eye className="h-4 w-4" />
              <span>VIEW_PROTOCOL</span>
            </Button>
          </Link>

          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                aria-label={`Delete ${report.title}`}
                size="sm"
                variant="ghost"
                className="!p-2 h-8 w-8 !rounded-full text-red-400/40 hover:bg-red-500/10 hover:text-red-300 transition-all"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent className="glass-modal">
              <AlertDialogHeader>
                <AlertDialogTitle className="text-[20px]">Purge Record?</AlertDialogTitle>
                <AlertDialogDescription className="text-[var(--text-secondary)]">
                  This action permanently deletes the report metadata and generated content from your workspace.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter className="mt-6">
                <AlertDialogCancel className="bg-transparent border-white/10 text-[var(--text-secondary)] hover:bg-white/05 hover:text-white rounded-[var(--radius-md)]">
                  CANCEL
                </AlertDialogCancel>
                <AlertDialogAction
                  className="bg-red-500/20 border border-red-500/30 text-red-300 hover:bg-red-500/30 rounded-[var(--radius-md)]"
                  disabled={isDeleting}
                  onClick={(event) => {
                    event.preventDefault();
                    void handleDelete();
                  }}
                >
                  PURGE_ASSET
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-4 relative z-10">
        <span className="rounded-full bg-white/05 border border-white/05 px-3 py-0.5 text-[10px] font-bold uppercase tracking-[0.1em] text-[var(--text-tertiary)] font-mono">
          TYPE: {formatReportType(report.report_type)}
        </span>
        <div className="h-1 w-1 rounded-full bg-white/10"></div>
        <span className="text-[11px] text-[var(--text-tertiary)] font-medium font-mono uppercase">
          {formatReportDate(report.created_at)}
        </span>
        {report.word_count ? (
          <>
            <div className="h-1 w-1 rounded-full bg-white/10"></div>
            <span className="text-[11px] text-[var(--text-tertiary)] font-bold font-mono uppercase">{report.word_count.toLocaleString()} WORDS</span>
          </>
        ) : null}
      </div>
    </article>
  );
};

export const ReportList = ({ initialData }: ReportListProps): JSX.Element => {
  const { token } = useSupabaseAccessToken();
  const [data, setData] = useState(initialData);
  const [isLoading, setIsLoading] = useState(false);
  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(data.total / data.page_size)),
    [data.page_size, data.total],
  );

  const loadPage = async (page: number): Promise<void> => {
    if (!token || page < 1 || page > totalPages) {
      return;
    }

    try {
      setIsLoading(true);
      setData(await getReports(token, page, data.page_size));
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to load reports.";
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleted = (reportId: string): void => {
    setData((current) => ({
      ...current,
      items: current.items.filter((report) => report.id !== reportId),
      total: Math.max(0, current.total - 1),
    }));
  };

  if (!isLoading && data.items.length === 0) {
    return (
      <div className="glass-card border-dashed p-16 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-[var(--radius-xl)] bg-white/05 text-[var(--text-tertiary)]">
          <FileText className="h-8 w-8" />
        </div>
        <h2 className="mt-8 text-[20px] font-semibold text-[var(--text-primary)]">
          Your library is empty
        </h2>
        <p className="mt-2 text-[15px] text-[var(--text-secondary)]">Generate a report to see it appear here.</p>
        <Link href="/generate" passHref legacyBehavior>
          <Button
            className="mt-8"
            variant="primary"
          >
            New report
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {isLoading ? (
        <>
          <ReportCardSkeleton />
          <ReportCardSkeleton />
          <ReportCardSkeleton />
        </>
      ) : (
        data.items.map((report) => (
          <ReportCard
            key={report.id}
            onDeleted={handleDeleted}
            report={report}
          />
        ))
      )}

      <div className="flex items-center justify-center gap-6 pt-10">
        <Button
          variant="secondary"
          size="sm"
          disabled={data.page <= 1 || isLoading}
          onClick={() => {
            void loadPage(data.page - 1);
          }}
        >
          Previous
        </Button>
        <span className="text-[11px] font-mono font-medium uppercase tracking-[0.1em] text-[var(--text-tertiary)]">
          {data.page} <span className="opacity-30">/</span> {totalPages}
        </span>
        <Button
          variant="secondary"
          size="sm"
          disabled={data.page >= totalPages || isLoading}
          onClick={() => {
            void loadPage(data.page + 1);
          }}
        >
          Next
        </Button>
      </div>
    </div>
  );
};
