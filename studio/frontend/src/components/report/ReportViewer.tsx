"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, ArrowUp, Copy, Download, RefreshCw, Trash2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";
import { toast } from "sonner";

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
  getPdfUrl,
  type Report,
} from "@/lib/api/reports";
import {
  formatReportDate,
  formatReportType,
  truncateText,
} from "@/lib/report-helpers";
import { cn } from "@/lib/utils";

import { ReportStatusBadge } from "./ReportStatusBadge";

interface ReportViewerProps {
  report: Report;
  onDelete?: () => void;
}

const metadataItemClass =
  "text-sm text-slate-500 dark:text-slate-400";

const ReportSkeleton = (): JSX.Element => (
  <div
    aria-label="Report loading"
    className="space-y-4 rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
    data-testid="report-skeleton"
  >
    <div className="h-4 w-11/12 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
    <div className="h-4 w-2/3 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
    <div className="h-4 w-5/6 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
  </div>
);

export const ReportViewer = ({
  onDelete,
  report,
}: ReportViewerProps): JSX.Element => {
  const router = useRouter();
  const { token } = useSupabaseAccessToken();
  const [showBackToTop, setShowBackToTop] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const pdfUrl = useMemo(() => getPdfUrl(report.id), [report.id]);
  const displayTitle = truncateText(report.title || report.topic, 60);

  useEffect(() => {
    const handleScroll = (): void => {
      setShowBackToTop(window.scrollY > 400);
    };

    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleCopy = async (): Promise<void> => {
    if (!report.content_md) {
      toast.error("No markdown is available to copy.");
      return;
    }

    try {
      await navigator.clipboard.writeText(report.content_md);
      toast.success("Copied!", { duration: 2000 });
    } catch {
      toast.error("Unable to copy markdown.");
    }
  };

  const handleDelete = async (): Promise<void> => {
    if (!token) {
      toast.error("Your session is not ready yet.");
      return;
    }

    try {
      setIsDeleting(true);
      await deleteReport(token, report.id);
      toast.success("Report deleted.");
      if (onDelete) {
        onDelete();
      } else {
        router.push("/dashboard");
      }
      router.refresh();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to delete report.";
      toast.error(message);
    } finally {
      setIsDeleting(false);
    }
  };

  const scrollToTop = (): void => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-50">
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-950/95">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-4 sm:px-6 lg:px-8">
          <div className="grid gap-3 lg:grid-cols-[auto_minmax(0,1fr)_auto] lg:items-center">
            <Link
              aria-label="Back to dashboard"
              className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 text-slate-700 transition hover:bg-slate-100 dark:border-slate-800 dark:text-slate-200 dark:hover:bg-slate-900"
              href="/dashboard"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>

            <div className="min-w-0 text-center lg:text-left">
              <h1
                className="truncate text-lg font-semibold text-slate-950 dark:text-slate-50 sm:text-xl"
                title={report.title || report.topic}
              >
                {displayTitle}
              </h1>
              <div className="mt-2 flex justify-center lg:justify-start">
                <ReportStatusBadge status={report.status} />
              </div>
            </div>

            <div className="flex flex-wrap justify-center gap-2 lg:justify-end">
              <button
                className="inline-flex h-10 items-center gap-2 rounded-lg border border-slate-200 px-3 text-sm font-medium text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-800 dark:text-slate-200 dark:hover:bg-slate-900"
                disabled={!report.content_md}
                onClick={() => {
                  void handleCopy();
                }}
                type="button"
              >
                <Copy className="h-4 w-4" />
                Copy markdown
              </button>

              <a
                className={cn(
                  "inline-flex h-10 items-center gap-2 rounded-lg border border-slate-200 px-3 text-sm font-medium text-slate-700 transition hover:bg-slate-100 dark:border-slate-800 dark:text-slate-200 dark:hover:bg-slate-900",
                  report.status !== "done" && "pointer-events-none opacity-50",
                )}
                download
                href={pdfUrl}
                rel="noreferrer"
                target="_blank"
              >
                <Download className="h-4 w-4" />
                Download PDF
              </a>

              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <button
                    className="inline-flex h-10 items-center gap-2 rounded-lg border border-red-200 px-3 text-sm font-medium text-red-700 transition hover:bg-red-50 dark:border-red-900 dark:text-red-300 dark:hover:bg-red-950"
                    type="button"
                  >
                    <Trash2 className="h-4 w-4" />
                    Delete
                  </button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete this report?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This removes the report from your history. This action
                      cannot be undone.
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

          <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 border-t border-slate-100 pt-3 dark:border-slate-900 lg:justify-start">
            <span className={metadataItemClass}>
              {formatReportType(report.report_type)}
            </span>
            {report.word_count ? (
              <span className={metadataItemClass}>
                {report.word_count.toLocaleString()} words
              </span>
            ) : null}
            <span className={metadataItemClass}>
              Created: {formatReportDate(report.created_at)}
            </span>
            <span className={metadataItemClass}>
              Completed: {formatReportDate(report.completed_at)}
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        {report.status === "pending" || report.status === "running" ? (
          <ReportSkeleton />
        ) : null}

        {report.status === "failed" ? (
          <section className="rounded-lg border border-red-200 bg-red-50 p-6 dark:border-red-900 dark:bg-red-950/40">
            <h2 className="text-lg font-semibold text-red-900 dark:text-red-100">
              Generation failed
            </h2>
            <p className="mt-2 text-sm text-red-700 dark:text-red-200">
              Report generation failed. Your credit has been refunded.
            </p>
            <Link
              className="mt-5 inline-flex h-10 items-center gap-2 rounded-lg bg-red-600 px-4 text-sm font-medium text-white transition hover:bg-red-700"
              href="/generate"
            >
              <RefreshCw className="h-4 w-4" />
              Try again
            </Link>
          </section>
        ) : null}

        {report.status === "done" && report.content_md ? (
          <article className="prose prose-neutral max-w-none rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950 dark:prose-invert sm:p-8">
            <ReactMarkdown
              rehypePlugins={[rehypeHighlight]}
              remarkPlugins={[remarkGfm]}
            >
              {report.content_md}
            </ReactMarkdown>
          </article>
        ) : null}
      </main>

      {showBackToTop ? (
        <button
          className="fixed bottom-6 right-6 z-50 inline-flex h-11 items-center gap-2 rounded-lg bg-slate-950 px-4 text-sm font-medium text-white shadow-lg transition hover:bg-slate-800 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
          onClick={scrollToTop}
          type="button"
        >
          <ArrowUp className="h-4 w-4" />
          Back to top
        </button>
      ) : null}
    </div>
  );
};
