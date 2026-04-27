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
    <aside className="flex w-full max-w-72 flex-col border-r border-slate-200/70 bg-white/70 p-5 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/70">
      <div className="flex items-center gap-3 rounded-2xl bg-brand-ink px-4 py-3 text-white shadow-panel dark:bg-slate-900">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-gold text-slate-950">
          <PanelLeftDashed className="h-5 w-5" />
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/70">
            CrewAI Studio
          </p>
          <h1 className="font-semibold">Report Forge</h1>
        </div>
      </div>

      <nav className="mt-8 flex flex-1 flex-col gap-2">
        {navigationItems.map(({ href, icon: Icon, label }) => {
          const isActive = pathname === href;

          return (
            <Link
              className={[
                "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all",
                isActive
                  ? "bg-brand-mist text-brand-ink shadow-sm dark:bg-slate-800 dark:text-white"
                  : "text-slate-600 hover:bg-white hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-900 dark:hover:text-white",
              ].join(" ")}
              href={href}
              key={href}
            >
              <Icon className="h-4 w-4" />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-6 rounded-2xl border border-slate-200/70 bg-white/80 p-4 dark:border-slate-800 dark:bg-slate-900/80">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">
              {user.email}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Active workspace
            </p>
          </div>
          <Badge variant={user.tier}>{user.tier}</Badge>
        </div>
        <Button
          className="mt-4 w-full"
          onClick={onLogout}
          size="sm"
          variant="ghost"
        >
          <LogOut className="h-4 w-4" />
          Logout
        </Button>
      </div>
    </aside>
  );
};
