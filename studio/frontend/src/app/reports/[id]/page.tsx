import Link from "next/link";
import { redirect } from "next/navigation";

import { ReportPolling } from "@/components/report/ReportPolling";
import { ReportViewer } from "@/components/report/ReportViewer";
import { ApiError } from "@/lib/api/client";
import { getJob } from "@/lib/api/jobs";
import { getReport, type ReportStatus } from "@/lib/api/reports";
import { getServerSupabaseAccessToken } from "@/lib/supabase/server";

interface ReportPageProps {
  params: {
    id: string;
  };
}

const ReportNotFound = (): JSX.Element => (
  <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-950">
    <div className="max-w-md text-center">
      <h1 className="text-2xl font-semibold text-slate-950 dark:text-slate-50">
        Report not found
      </h1>
      <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
        The report may have been deleted, or you may not have access to it.
      </p>
      <Link
        className="mt-6 inline-flex h-10 items-center justify-center rounded-lg bg-slate-950 px-4 text-sm font-medium text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
        href="/dashboard"
      >
        Back to dashboard
      </Link>
    </div>
  </main>
);

export default async function ReportPage({
  params,
}: ReportPageProps): Promise<JSX.Element> {
  const token = await getServerSupabaseAccessToken();
  if (!token) {
    redirect("/login");
  }

  try {
    const report = await getReport(token, params.id);
    let pollingStatus: ReportStatus = report.status;

    if (
      (report.status === "pending" || report.status === "running") &&
      report.job_id
    ) {
      try {
        const job = await getJob(token, report.job_id);
        pollingStatus = job.status;
      } catch {
        pollingStatus = report.status;
      }
    }

    return (
      <>
        {report.job_id &&
        (report.status === "pending" || report.status === "running") ? (
          <ReportPolling
            initialStatus={pollingStatus}
            jobId={report.job_id}
            reportId={report.id}
          />
        ) : null}
        <ReportViewer report={report} />
      </>
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return <ReportNotFound />;
    }
    throw error;
  }
}
