import Link from "next/link";
import { redirect } from "next/navigation";

import { ReportList } from "@/components/report/ReportList";
import { ApiError } from "@/lib/api/client";
import { getUsageSummary, type UsageSummary } from "@/lib/api/billing";
import { getReports } from "@/lib/api/reports";
import { formatReportDate } from "@/lib/report-helpers";
import { getServerSupabaseAccessToken } from "@/lib/supabase/server";

const formatUsageLine = (usage: UsageSummary): string => {
  const resetDate = formatReportDate(usage.resets_on);
  if (usage.monthly_limit === null) {
    return `You have used ${usage.reports_this_month} reports this month. Resets on ${resetDate}.`;
  }

  return `You have used ${usage.reports_this_month} of ${usage.monthly_limit} reports this month. Resets on ${resetDate}.`;
};

export default async function DashboardPage(): Promise<JSX.Element> {
  const token = await getServerSupabaseAccessToken();
  if (!token) {
    redirect("/login");
  }

  try {
    const [reports, usage] = await Promise.all([
      getReports(token, 1, 10),
      getUsageSummary(token),
    ]);
    const freeLimitReached =
      usage.tier === "free" &&
      usage.monthly_limit !== null &&
      usage.reports_this_month >= usage.monthly_limit;

    return (
      <main className="min-h-screen bg-slate-50 px-4 py-8 text-slate-950 dark:bg-slate-950 dark:text-slate-50 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-6xl space-y-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-semibold tracking-tight">
                Your reports
              </h1>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                Review, export, or remove generated reports from your workspace.
              </p>
            </div>
            <Link
              className="inline-flex h-10 items-center justify-center rounded-lg bg-slate-950 px-4 text-sm font-medium text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
              href="/generate"
            >
              New report
            </Link>
          </div>

          <section className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-700 shadow-sm dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200">
            {formatUsageLine(usage)}
          </section>

          {freeLimitReached ? (
            <section className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
              Your free plan is at its monthly report limit. Upgrade to keep
              generating reports without waiting for the reset date.
            </section>
          ) : null}

          <ReportList initialData={reports} />
        </div>
      </main>
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      redirect("/login");
    }
    throw error;
  }
}
