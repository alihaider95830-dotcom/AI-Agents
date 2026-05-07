"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, ArrowUp, Copy, Download, RefreshCw, Trash2, Calendar, FileText, BarChart } from "lucide-react";
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
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
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
  "flex items-center gap-1.5 text-[12px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider";

const ReportSkeleton = (): JSX.Element => (
  <div
    aria-label="Report loading"
    className="glass-card p-10 space-y-6 animate-pulse"
    data-testid="report-skeleton"
  >
    <div className="h-6 w-1/2 rounded bg-white/05" />
    <div className="space-y-3">
      <div className="h-4 w-full rounded bg-white/05" />
      <div className="h-4 w-[95%] rounded bg-white/05" />
      <div className="h-4 w-[90%] rounded bg-white/05" />
    </div>
    <div className="h-4 w-2/3 rounded bg-white/05" />
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
  const displayTitle = truncateText(report.title || report.topic, 80);

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
      toast.success("Copied to clipboard");
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
    <div className="min-h-screen text-[var(--text-primary)]">
      <header className="sticky top-0 z-40 border-b border-[var(--border-dim)] bg-black/60 backdrop-blur-xl relative overflow-hidden glass-scanline">
        <div className="mx-auto flex max-w-6xl flex-col gap-6 px-8 py-8 lg:px-10 relative z-10">
          <div className="grid gap-6 lg:grid-cols-[auto_minmax(0,1fr)_auto] lg:items-center">
            <Link href="/dashboard" passHref legacyBehavior>
              <Button
                aria-label="Back to dashboard"
                size="sm"
                variant="secondary"
                className="!h-10 !w-10 !rounded-full !bg-white/05 hover:!bg-white/10"
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>

            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-4">
                <h1
                  className="text-[24px] font-semibold tracking-tight text-white leading-tight"
                  title={report.title || report.topic}
                >
                  {displayTitle}
                </h1>
                <ReportStatusBadge status={report.status} />
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button
                size="sm"
                variant="secondary"
                className="btn-glow !bg-white/05 hover:!bg-white/10 border-white/05"
                disabled={!report.content_md}
                onClick={() => {
                  void handleCopy();
                }}
              >
                <Copy className="h-4 w-4 mr-2 opacity-60" />
                Copy Markdown
              </Button>

              <a
                className={cn(
                  report.status !== "done" && "pointer-events-none opacity-50",
                )}
                download
                href={pdfUrl}
                rel="noreferrer"
                target="_blank"
              >
                <Button variant="primary" size="sm" disabled={report.status !== "done"} className="btn-glow !rounded-full px-6">
                  <Download className="h-4 w-4 mr-2" />
                  Download PDF
                </Button>
              </a>

              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="!p-2 h-10 w-10 !rounded-full text-red-400/60 hover:bg-red-500/10 hover:text-red-300 transition-all duration-300"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent className="glass-modal border-white/10 shadow-2xl">
                  <AlertDialogHeader>
                    <AlertDialogTitle className="text-[22px] tracking-tight">Confirm Deletion</AlertDialogTitle>
                    <AlertDialogDescription className="text-[var(--text-secondary)] leading-relaxed">
                      This action will permanently purge this synthetic asset from your repository. 
                      This operation is irreversible.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter className="mt-8">
                    <AlertDialogCancel className="bg-transparent border-white/05 text-[var(--text-secondary)] hover:bg-white/05 hover:text-white rounded-[var(--radius-md)] transition-colors">
                      Cancel
                    </AlertDialogCancel>
                    <AlertDialogAction
                      className="bg-red-500/20 border border-red-500/30 text-red-300 hover:bg-red-500/30 rounded-[var(--radius-md)] transition-colors"
                      disabled={isDeleting}
                      onClick={(event) => {
                        event.preventDefault();
                        void handleDelete();
                      }}
                    >
                      Purge Asset
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-x-8 gap-y-3 border-t border-white/05 pt-6">
            <div className={metadataItemClass}>
              <BarChart className="h-3.5 w-3.5 opacity-40" />
              <span className="opacity-60">TYPE:</span>
              <span className="text-white/80">{formatReportType(report.report_type)}</span>
            </div>
            {report.word_count ? (
              <div className={metadataItemClass}>
                <FileText className="h-3.5 w-3.5 opacity-40" />
                <span className="opacity-60">LENGTH:</span>
                <span className="font-mono text-white/80">{report.word_count.toLocaleString()} WORDS</span>
              </div>
            ) : null}
            <div className={metadataItemClass}>
              <Calendar className="h-3.5 w-3.5 opacity-40" />
              <span className="opacity-60">CREATED:</span>
              <span className="font-mono text-white/80">{formatReportDate(report.created_at)}</span>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-8 py-16 lg:px-10">
        {report.status === "pending" || report.status === "running" ? (
          <ReportSkeleton />
        ) : null}

        {report.status === "failed" ? (
          <section className="glass-elevated p-12 border-red-500/20 bg-red-500/[0.02] animate-glass-enter text-center">
            <div className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-red-500/10 mb-6">
              <RefreshCw className="h-8 w-8 text-red-400" />
            </div>
            <h2 className="text-[26px] font-semibold text-white tracking-tight">
              Operational Failure
            </h2>
            <p className="mt-4 text-[16px] leading-relaxed text-[var(--text-secondary)] max-w-xl mx-auto">
              The AI crew encountered an unrecoverable error during synthesis. 
              Your operational credits have been automatically restored.
            </p>
            <Link href="/generate" passHref legacyBehavior>
              <Button
                className="mt-10 !rounded-full px-10"
                variant="secondary"
              >
                Re-initiate Protocol
              </Button>
            </Link>
          </section>
        ) : null}

        {report.status === "done" && report.content_md ? (
          <article className="glass-card !bg-white/[0.01] border-white/05 p-12 sm:p-20 animate-glass-enter shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-white/10 to-transparent" />
            <div className="prose prose-zinc prose-report max-w-none relative z-10">
              <ReactMarkdown
                rehypePlugins={[rehypeHighlight]}
                remarkPlugins={[remarkGfm]}
              >
                {report.content_md}
              </ReactMarkdown>
            </div>
          </article>
        ) : null}
      </main>

      {showBackToTop ? (
        <Button
          className="fixed bottom-12 right-12 z-50 !rounded-full shadow-2xl btn-glow animate-glass-enter"
          onClick={scrollToTop}
          variant="primary"
        >
          <ArrowUp className="h-4 w-4 mr-2" />
          BACK_TO_TOP
        </Button>
      ) : null}
    </div>
  );
};
