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
        <LoaderCircle className="h-10 w-10 animate-spin text-brand-ocean dark:text-brand-gold" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      <Sidebar onLogout={logout} user={user} />
      <div className="flex min-h-screen flex-1 flex-col">
        <Topbar user={user} />
        <PaymentWarningBoundary />
        <main className="flex-1 bg-white/50 p-6 dark:bg-slate-950/40">
          {children}
        </main>
      </div>
    </div>
  );
}
