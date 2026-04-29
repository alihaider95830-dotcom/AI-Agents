const LAST_UPDATED = "April 27, 2026";

export default function TermsOfServicePage(): JSX.Element {
  return (
    <main className="mx-auto min-h-screen w-full max-w-3xl px-4 py-16 sm:px-6">
      <article className="prose prose-neutral max-w-none">
        <h1>Terms of Service</h1>
        <p>
          <strong>Last updated:</strong> {LAST_UPDATED}
        </p>

        <h2>Acceptable use</h2>
        <p>Do not use Studio for illegal content or automated scraping of Studio services.</p>

        <h2>Output ownership</h2>
        <p>You own the reports you generate with Studio.</p>

        <h2>Liability</h2>
        <p>
          Studio is provided as-is. We do not guarantee that every generated statement is fully
          accurate.
        </p>

        <h2>Cancellation</h2>
        <p>Paid plans can be cancelled anytime. We do not offer refunds for partial months.</p>

        <h2>Contact</h2>
        <p>Questions about terms can be sent to legal@yourdomain.com.</p>
      </article>
    </main>
  );
}
