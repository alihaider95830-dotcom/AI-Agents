"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  FileText,
  LogOut,
  PanelLeftDashed,
  Settings,
  Sparkles,
} from "lucide-react";

import type { User } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

interface SidebarProps {
  user: User;
  onLogout: () => void;
}

const navigationItems = [
  {
    href: "/generate",
    icon: Sparkles,
    label: "Generate",
  },
  {
    href: "/dashboard",
    icon: FileText,
    label: "Reports",
  },
  {
    href: "/settings",
    icon: Settings,
    label: "Settings",
  },
];

export const Sidebar = ({ onLogout, user }: SidebarProps): JSX.Element => {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-full max-w-[240px] flex-col border-r border-[var(--border-dim)] bg-white/[0.03] p-[var(--space-4)] backdrop-blur-md glass-scanline relative overflow-hidden">
      <div className="flex items-center gap-3 px-2 py-6 relative z-10">
        <div className="flex h-9 w-9 items-center justify-center rounded-[var(--radius-md)] bg-white text-[var(--text-inverse)] shadow-[0_0_20px_rgba(255,255,255,0.2)]">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 2 22 22 22"></polygon></svg>
        </div>
        <div>
          <h1 className="text-[17px] font-semibold tracking-tight text-white">Studio</h1>
          <p className="text-[10px] uppercase tracking-[0.25em] text-[var(--text-tertiary)] font-medium">
            AI WORKSPACE
          </p>
        </div>
      </div>

      <nav className="mt-6 flex flex-1 flex-col gap-1 relative z-10">
        {navigationItems.map(({ href, icon: Icon, label }) => {
          const isActive = pathname === href;

          return (
            <Link
              className={[
                "flex items-center gap-3 rounded-[var(--radius-md)] px-3 py-2 text-[14px] transition-all duration-300",
                isActive
                  ? "bg-white/[0.08] border border-white/[0.1] text-white font-medium shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]"
                  : "text-[var(--text-secondary)] hover:bg-white/[0.04] hover:text-[var(--text-primary)]",
              ].join(" ")}
              href={href}
              key={href}
            >
              <Icon className={["h-4 w-4 stroke-[1.5px]", isActive ? "text-white" : "text-[var(--text-tertiary)]"].join(" ")} />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto pt-6 border-t border-[var(--border-dim)] relative z-10">
        <div className="glass-card p-[var(--space-4)] !bg-white/[0.02] border-white/[0.05]">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="truncate text-[13px] font-medium text-white">
                {user.email}
              </p>
              <p className="text-[10px] text-[var(--text-tertiary)] uppercase tracking-[0.15em] mt-1 font-semibold">
                {user.tier} PLAN
              </p>
            </div>
            <Badge variant={user.tier} className="!text-[9px] !px-2 !py-0.5">{user.tier}</Badge>
          </div>
          <Button
            className="mt-4 w-full justify-start !px-0 btn-glow"
            onClick={onLogout}
            size="sm"
            variant="ghost"
          >
            <LogOut className="h-4 w-4 mr-2 text-[var(--text-tertiary)]" />
            <span className="text-[13px]">Logout</span>
          </Button>
        </div>
      </div>
    </aside>
  );
};
