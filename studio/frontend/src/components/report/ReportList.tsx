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
    className="h-36 animate-pulse rounded-lg border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950"
    data-testid="report-card-skeleton"
  >
    <div className="h-4 w-1/3 rounded bg-slate-200 dark:bg-slate-800" />
    <div className="mt-4 h-3 w-3/4 rounded bg-slate-200 dark:bg-slate-800" />
    <div className="mt-6 h-8 w-full rounded bg-slate-200 dark:bg-slate-800" />
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
    <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:border-slate-300 dark:border-slate-800 dark:bg-slate-950 dark:hover:border-slate-700">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="truncate text-base font-semibold text-slate-950 dark:text-slate-50">
              {report.title}
            </h2>
            <ReportStatusBadge status={report.status} />
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
            {truncateText(report.topic, 80)}
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <Link
            aria-label={`View ${report.title}`}
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-700 transition hover:bg-slate-100 dark:border-slate-800 dark:text-slate-200 dark:hover:bg-slate-900"
            href={`/reports/${report.id}`}
          >
            <Eye className="h-4 w-4" />
          </Link>

          <AlertDialog>
            <AlertDialogTrigger asChild>
              <button
                aria-label={`Delete ${report.title}`}
                className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-red-200 text-red-700 transition hover:bg-red-50 dark:border-red-900 dark:text-red-300 dark:hover:bg-red-950"
                type="button"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete this report?</AlertDialogTitle>
                <AlertDialogDescription>
                  This removes the report from your history. This action cannot
                  be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel className="inline-flex h-10 items-center justify-center rounded-lg border border-slate-200 px-4 text-sm font-medium text-slate-700 transition hover:bg-slate-100 dark:border-slate-800 dark:text-slate-200 dark:hover:bg-slate-900">
                  Cancel
                </AlertDialogCancel>
                <AlertDialogAction
                  className="inline-flex h-10 items-center justify-center rounded-lg bg-red-600 px-4 text-sm font-medium text-white transition hover:bg-red-700 disabled:opacity-50"
                  disabled={isDeleting}
                  onClick={(event) => {
                    event.preventDefault();
                    void handleDelete();
                  }}
                >
                  Delete report
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
        <span className="rounded-full bg-slate-100 px-2.5 py-1 font-medium text-slate-700 dark:bg-slate-900 dark:text-slate-200">
          {formatReportType(report.report_type)}
        </span>
        <span>{formatReportDate(report.created_at)}</span>
        {report.word_count ? (
          <span>{report.word_count.toLocaleString()} words</span>
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
      <div className="rounded-lg border border-dashed border-slate-300 bg-white p-10 text-center dark:border-slate-700 dark:bg-slate-950">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-slate-100 text-slate-500 dark:bg-slate-900 dark:text-slate-400">
          <FileText className="h-7 w-7" />
        </div>
        <h2 className="mt-5 text-lg font-semibold text-slate-950 dark:text-slate-50">
          No reports yet
        </h2>
        <Link
          className="mt-5 inline-flex h-10 items-center justify-center rounded-lg bg-slate-950 px-4 text-sm font-medium text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
          href="/generate"
        >
          Generate your first report
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

      <div className="flex items-center justify-center gap-3 pt-2">
        <button
          className="inline-flex h-10 items-center justify-center rounded-lg border border-slate-200 px-4 text-sm font-medium text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-800 dark:text-slate-200 dark:hover:bg-slate-900"
          disabled={data.page <= 1 || isLoading}
          onClick={() => {
            void loadPage(data.page - 1);
          }}
          type="button"
        >
          Previous
        </button>
        <span className="text-sm text-slate-500 dark:text-slate-400">
          Page {data.page} of {totalPages}
        </span>
        <button
          className="inline-flex h-10 items-center justify-center rounded-lg border border-slate-200 px-4 text-sm font-medium text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-800 dark:text-slate-200 dark:hover:bg-slate-900"
          disabled={data.page >= totalPages || isLoading}
          onClick={() => {
            void loadPage(data.page + 1);
          }}
          type="button"
        >
          Next
        </button>
      </div>
    </div>
  );
};
