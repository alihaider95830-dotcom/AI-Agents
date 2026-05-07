import Link from "next/link";
import { Github, Twitter } from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function Footer(): JSX.Element {
  return (
    <footer className="px-6 pb-16 pt-24">
      <div className="mx-auto w-full max-w-6xl border-t border-white/05 pt-16">
        <div className="grid gap-12 md:grid-cols-[1.5fr_0.9fr_0.9fr]">
          <div>
            <div className="flex items-center gap-3 text-[18px] font-semibold tracking-tight text-white">
              <div className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-md)] bg-white text-[var(--text-inverse)] shadow-lg shadow-white/10">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 2 22 22 22"></polygon></svg>
              </div>
              Studio
            </div>
            <p className="mt-4 max-w-xs text-[15px] leading-relaxed text-[var(--text-secondary)]">AI agents that write your market research with structure, citations, and speed.</p>
            <p className="mt-8 text-[13px] text-[var(--text-tertiary)] font-medium uppercase tracking-wider">© 2026 Studio. All rights reserved.</p>
          </div>

          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.25em] text-white/40">Product</p>
            <ul className="mt-6 space-y-4 text-[14px] text-[var(--text-secondary)]">
              <li>
                <Link href="#features" className="transition-colors hover:text-white">
                  Features
                </Link>
              </li>
              <li>
                <Link href="/pricing" className="transition-colors hover:text-white">
                  Pricing
                </Link>
              </li>
              <li>
                <Link href="#example-report" className="transition-colors hover:text-white">
                  Sample report
                </Link>
              </li>
              <li>
                <Link href="/generate" className="transition-colors hover:text-white">
                  Generate
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.25em] text-white/40">Legal &amp; Support</p>
            <ul className="mt-6 space-y-4 text-[14px] text-[var(--text-secondary)]">
              <li>
                <Link href="/legal/privacy" className="transition-colors hover:text-white">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/legal/terms" className="transition-colors hover:text-white">
                  Terms of Service
                </Link>
              </li>
              <li>
                <a href="mailto:hello@yourdomain.com" className="transition-colors hover:text-white">
                  Contact
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-16 flex flex-col gap-6 border-t border-white/05 pt-10 text-[13px] text-[var(--text-tertiary)] sm:flex-row sm:items-center sm:justify-between">
          <p className="font-medium">Built with CrewAI, FastAPI, and Next.js</p>
          <div className="flex items-center gap-4">
            <a
              href="https://twitter.com/yourhandle"
              target="_blank"
              rel="noreferrer"
              aria-label="Studio on Twitter"
            >
              <Button variant="secondary" size="sm" className="!h-9 !w-9 !p-0 !rounded-full">
                <Twitter className="h-4 w-4" aria-hidden="true" />
              </Button>
            </a>
            <a
              href="https://github.com/yourrepo"
              target="_blank"
              rel="noreferrer"
              aria-label="Studio on GitHub"
            >
              <Button variant="secondary" size="sm" className="!h-9 !w-9 !p-0 !rounded-full">
                <Github className="h-4 w-4" aria-hidden="true" />
              </Button>
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
