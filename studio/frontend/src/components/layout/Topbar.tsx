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
    <header className="flex flex-col gap-4 border-b border-[var(--border-dim)] bg-black/40 px-8 py-6 backdrop-blur-md md:flex-row md:items-center md:justify-between relative overflow-hidden glass-scanline">
      <div className="relative z-10">
        <p className="text-[10px] uppercase tracking-[0.3em] text-[var(--text-tertiary)] font-semibold">
          SYSTEM_NODE / {title.toUpperCase().replace(" ", "_")}
        </p>
        <h2 className="mt-1 text-[22px] font-semibold tracking-tight text-white">
          {title}
        </h2>
      </div>

      <div className="flex items-center gap-4 relative z-10">
        <div className="flex items-center gap-2.5 px-4 py-2 rounded-full border border-white/05 bg-white/[0.03] shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
          <span className="h-1.5 w-1.5 rounded-full bg-white shadow-[0_0_10px_rgba(255,255,255,0.8)] animate-pulse" />
          <span className="text-[11px] font-medium uppercase tracking-[0.1em] text-[var(--text-secondary)] font-mono">
            CREDITS_REMAINING: <span className="text-white">{user.credits}</span>
          </span>
        </div>
        
        <Button
          aria-label="Toggle theme"
          className="rounded-full !p-2 h-10 w-10 btn-glow border-white/05 bg-white/[0.03]"
          onClick={() => setTheme(isDark ? "light" : "dark")}
          size="sm"
          variant="secondary"
        >
          {isDark ? (
            <SunMedium className="h-4 w-4 text-[var(--text-secondary)]" />
          ) : (
            <MoonStar className="h-4 w-4 text-[var(--text-secondary)]" />
          )}
        </Button>
      </div>
    </header>
  );
};
