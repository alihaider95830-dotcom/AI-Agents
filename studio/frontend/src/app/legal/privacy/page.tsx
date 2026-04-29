const LAST_UPDATED = "April 27, 2026";

export default function PrivacyPolicyPage(): JSX.Element {
  return (
    <main className="mx-auto min-h-screen w-full max-w-3xl px-4 py-16 sm:px-6">
      <article className="prose prose-neutral max-w-none">
        <h1>Privacy Policy</h1>
        <p>
          <strong>Last updated:</strong> {LAST_UPDATED}
        </p>

        <h2>What we collect</h2>
        <p>We collect your email address, usage data, and report topics.</p>

        <h2>How we use it</h2>
        <p>
          We use this information to provide the service, run report generation, and improve output
          quality and reliability.
        </p>

        <h2>What we do not do</h2>
        <p>We do not sell your data, and we do not train models on your report content.</p>

        <h2>Data retention</h2>
        <p>Reports are kept for 90 days after account deletion and then permanently removed.</p>

        <h2>Contact</h2>
        <p>Questions about privacy can be sent to privacy@yourdomain.com.</p>
      </article>
    </main>
  );
}
