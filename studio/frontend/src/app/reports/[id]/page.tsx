import Link from "next/link";
import { redirect } from "next/navigation";

import { ReportPolling } from "@/components/report/ReportPolling";
import { ReportViewer } from "@/components/report/ReportViewer";
import { Button } from "@/components/ui/Button";
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
  <main className="flex min-h-[60vh] items-center justify-center px-4">
    <div className="glass-elevated max-w-md p-10 text-center animate-glass-enter">
      <h1 className="text-[20px] font-semibold text-[var(--text-primary)]">
        Report not found
      </h1>
      <p className="mt-3 text-[15px] leading-relaxed text-[var(--text-secondary)]">
        The report may have been deleted, or you may not have access to it.
      </p>
      <Link href="/dashboard" passHref legacyBehavior>
        <Button
          className="mt-8"
          variant="primary"
        >
          Back to dashboard
        </Button>
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
