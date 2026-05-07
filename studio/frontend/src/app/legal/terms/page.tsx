import NavBar from "@/components/landing/NavBar";
import Footer from "@/components/landing/Footer";

const LAST_UPDATED = "April 27, 2026";

export default function TermsOfServicePage(): JSX.Element {
  return (
    <main className="bg-white text-zinc-900">
      <NavBar />
      
      <section className="px-4 py-16 sm:px-6 lg:py-24">
        <div className="mx-auto max-w-3xl">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-zinc-200/60 bg-white/50 px-3 py-1 text-xs font-medium text-zinc-600 shadow-[0_1px_2px_rgba(0,0,0,0.02)] backdrop-blur-sm">
            Legal
          </span>
          <h1 className="mt-8 text-4xl font-semibold tracking-tight text-zinc-900 sm:text-5xl">
            Terms of Service
          </h1>
          <p className="mt-4 text-sm text-zinc-500">
            <strong>Last updated:</strong> {LAST_UPDATED}
          </p>

          <div className="prose prose-zinc mt-12 max-w-none text-zinc-600">
            <h2 className="text-zinc-900">Acceptable use</h2>
            <p>Do not use Studio for illegal content or automated scraping of Studio services.</p>

            <h2 className="text-zinc-900">Output ownership</h2>
            <p>You own the reports you generate with Studio.</p>

            <h2 className="text-zinc-900">Liability</h2>
            <p>
              Studio is provided as-is. We do not guarantee that every generated statement is fully
              accurate.
            </p>

            <h2 className="text-zinc-900">Cancellation</h2>
            <p>Paid plans can be cancelled anytime. We do not offer refunds for partial months.</p>

            <h2 className="text-zinc-900">Contact</h2>
            <p>Questions about terms can be sent to legal@yourdomain.com.</p>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
