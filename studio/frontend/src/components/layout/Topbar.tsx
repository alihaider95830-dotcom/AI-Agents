"use client";

import { MoonStar, SunMedium } from "lucide-react";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";

import type { User } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

interface TopbarProps {
  user: User;
}

const pageTitles: Record<string, string> = {
  "/dashboard": "Reports Library",
  "/generate": "Generate Report",
  "/reports": "Reports Library",
  "/settings": "Workspace Settings",
};

export const Topbar = ({ user }: TopbarProps): JSX.Element => {
  const pathname = usePathname();
  const { resolvedTheme, setTheme } = useTheme();

  const title = pageTitles[pathname] ?? "Dashboard";
  const isDark = resolvedTheme === "dark";

  return (
    <header className="flex flex-col gap-4 border-b border-slate-200/70 bg-white/70 px-6 py-5 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/70 md:flex-row md:items-center md:justify-between">
      <div>
        <p className="text-xs uppercase tracking-[0.3em] text-slate-500 dark:text-slate-400">
          AI Report Platform
        </p>
        <h2 className="mt-1 text-2xl font-semibold text-slate-900 dark:text-slate-50">
          {title}
        </h2>
      </div>

      <div className="flex items-center gap-3">
        <Badge variant="default">{user.credits} credits</Badge>
        <Button
          aria-label="Toggle theme"
          onClick={() => setTheme(isDark ? "light" : "dark")}
          size="sm"
          variant="ghost"
        >
          {isDark ? (
            <SunMedium className="h-4 w-4" />
          ) : (
            <MoonStar className="h-4 w-4" />
          )}
        </Button>
      </div>
    </header>
  );
};
