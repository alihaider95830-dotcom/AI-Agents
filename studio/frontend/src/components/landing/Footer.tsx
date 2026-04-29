import Link from "next/link";
import { Github, Twitter } from "lucide-react";

export default function Footer(): JSX.Element {
  return (
    <footer className="px-4 pb-10 pt-12 sm:px-6">
      <div className="mx-auto w-full max-w-6xl border-t border-neutral-100 pt-12">
        <div className="grid gap-10 md:grid-cols-3">
          <div>
            <p className="text-lg font-medium text-neutral-900">Studio</p>
            <p className="mt-2 text-sm text-neutral-600">AI agents that write your market research.</p>
            <p className="mt-4 text-sm text-neutral-500">© 2025 Studio. All rights reserved.</p>
          </div>

          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-neutral-900">Product</p>
            <ul className="mt-4 space-y-2 text-sm text-neutral-600">
              <li>
                <Link href="#features" className="hover:text-neutral-900">
                  Features
                </Link>
              </li>
              <li>
                <Link href="/pricing" className="hover:text-neutral-900">
                  Pricing
                </Link>
              </li>
              <li>
                <Link href="#example-report" className="hover:text-neutral-900">
                  Sample report
                </Link>
              </li>
              <li>
                <Link href="/generate" className="hover:text-neutral-900">
                  Generate
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-neutral-900">Legal &amp; Support</p>
            <ul className="mt-4 space-y-2 text-sm text-neutral-600">
              <li>
                <Link href="/legal/privacy" className="hover:text-neutral-900">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/legal/terms" className="hover:text-neutral-900">
                  Terms of Service
                </Link>
              </li>
              <li>
                <a href="mailto:hello@yourdomain.com" className="hover:text-neutral-900">
                  Contact
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 flex flex-col gap-4 border-t border-neutral-100 pt-8 text-sm text-neutral-500 sm:flex-row sm:items-center sm:justify-between">
          <p>Built with CrewAI, FastAPI, and Next.js</p>
          <div className="flex items-center gap-3">
            <a
              href="https://twitter.com/yourhandle"
              target="_blank"
              rel="noreferrer"
              aria-label="Studio on Twitter"
              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-neutral-200 text-neutral-600 transition hover:bg-neutral-50 hover:text-neutral-900"
            >
              <Twitter className="h-4 w-4" aria-hidden="true" />
            </a>
            <a
              href="https://github.com/yourrepo"
              target="_blank"
              rel="noreferrer"
              aria-label="Studio on GitHub"
              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-neutral-200 text-neutral-600 transition hover:bg-neutral-50 hover:text-neutral-900"
            >
              <Github className="h-4 w-4" aria-hidden="true" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
