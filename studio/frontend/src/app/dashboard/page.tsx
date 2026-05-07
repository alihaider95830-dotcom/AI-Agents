import Link from "next/link";
import { redirect } from "next/navigation";

import { ReportList } from "@/components/report/ReportList";
import { Button } from "@/components/ui/Button";
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
      <div className="space-y-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-[26px] font-semibold tracking-tight text-[var(--text-primary)]">
              Reports Library
            </h1>
            <p className="mt-2 text-[15px] text-[var(--text-secondary)]">
              Review, export, or remove generated reports from your workspace.
            </p>
          </div>
          <Link href="/generate" passHref legacyBehavior>
            <Button variant="primary">
              New report
            </Button>
          </Link>
        </div>

        <section className="glass-card !bg-white/[0.02] p-5 text-[14px] text-[var(--text-secondary)]">
          <div className="flex items-center gap-3">
            <div className="h-1.5 w-1.5 rounded-full bg-white/20"></div>
            {formatUsageLine(usage)}
          </div>
        </section>

        {freeLimitReached ? (
          <section className="glass-elevated p-8 bg-white/[0.05] border-white/20">
            <h3 className="text-[20px] font-semibold text-[var(--text-primary)]">Monthly limit reached</h3>
            <p className="mt-2 text-[15px] text-[var(--text-secondary)] leading-relaxed">
              Your free plan is at its monthly report limit. Upgrade to Studio Pro to keep
              generating reports without waiting for the reset date.
            </p>
            <Link href="/pricing" passHref legacyBehavior>
              <Button 
                variant="primary"
                className="mt-8"
              >
                View Pro Plan
              </Button>
            </Link>
          </section>
        ) : null}

        <ReportList initialData={reports} />
      </div>
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      redirect("/login");
    }
    throw error;
  }
}
