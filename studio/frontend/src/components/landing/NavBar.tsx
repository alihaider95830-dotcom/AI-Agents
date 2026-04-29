"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

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
        "sticky top-0 z-50 transition-all duration-200",
        isScrolled
          ? "border-b border-neutral-200 bg-white/95 shadow-sm backdrop-blur"
          : "bg-transparent",
      ].join(" ")}
    >
      <nav className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="text-lg font-medium text-neutral-900">
          Studio
        </Link>

        <div className="flex items-center gap-3 sm:gap-4">
          <Link href="/pricing" className="hidden text-sm text-neutral-700 hover:text-neutral-900 sm:inline">
            Pricing
          </Link>
          <Link href="/auth/signin" className="hidden text-sm text-neutral-700 hover:text-neutral-900 sm:inline">
            Sign in
          </Link>
          <Link
            href="/auth/signup"
            className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-700"
          >
            Get started free
          </Link>
        </div>
      </nav>
    </header>
  );
}
