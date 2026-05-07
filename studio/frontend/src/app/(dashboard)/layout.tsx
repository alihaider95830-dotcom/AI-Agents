"use client";

import { useEffect } from "react";
import { LoaderCircle } from "lucide-react";
import { useRouter } from "next/navigation";

import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { PaymentWarningBoundary } from "@/components/billing/PaymentWarningBoundary";
import { useSession } from "@/hooks/useSession";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({
  children,
}: DashboardLayoutProps): JSX.Element {
  const router = useRouter();
  const { isAuthenticated, isLoading, logout, user } = useSession();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading || !isAuthenticated || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <LoaderCircle className="h-10 w-10 animate-spin text-white/20" />
          <p className="text-[11px] uppercase tracking-[0.2em] text-[var(--text-tertiary)] animate-pulse">
            Initializing Workspace
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      <Sidebar onLogout={logout} user={user} />
      <div className="flex min-h-screen flex-1 flex-col overflow-hidden">
        <Topbar user={user} />
        <div className="flex-1 overflow-y-auto">
          <PaymentWarningBoundary />
          <main className="p-8 max-w-[1400px] mx-auto w-full">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
