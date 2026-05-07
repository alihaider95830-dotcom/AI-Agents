"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";

export default function NavBar(): JSX.Element {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const onScroll = (): void => {
      setIsScrolled(window.scrollY > 8);
    };

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
    };
  }, []);

  return (
    <header
      className={[
        "sticky top-0 z-50 transition-all duration-300",
        isScrolled
          ? "border-b border-[var(--border-dim)] bg-black/40 backdrop-blur-xl"
          : "bg-transparent",
      ].join(" ")}
    >
      <nav className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-md)] bg-white text-[var(--text-inverse)] shadow-lg shadow-white/10">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 2 22 22 22"></polygon></svg>
          </div>
          <span className="text-[18px] font-semibold tracking-tight text-white">Studio</span>
        </Link>

        <div className="flex items-center gap-8">
          <Link href="/pricing" className="hidden text-[14px] font-medium text-[var(--text-secondary)] transition-colors hover:text-white sm:inline">
            Pricing
          </Link>
          <Link href="/auth/signin" className="hidden text-[14px] font-medium text-[var(--text-secondary)] transition-colors hover:text-white sm:inline">
            Sign in
          </Link>
          <Link href="/auth/signup" passHref legacyBehavior>
            <Button variant="primary" size="sm" className="!rounded-full px-6">
              Get started
            </Button>
          </Link>
        </div>
      </nav>
    </header>
  );
}
