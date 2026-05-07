import NavBar from "@/components/landing/NavBar";
import Footer from "@/components/landing/Footer";

const LAST_UPDATED = "April 27, 2026";

export default function PrivacyPolicyPage(): JSX.Element {
  return (
    <main className="bg-white text-zinc-900">
      <NavBar />
      
      <section className="px-4 py-16 sm:px-6 lg:py-24">
        <div className="mx-auto max-w-3xl">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-zinc-200/60 bg-white/50 px-3 py-1 text-xs font-medium text-zinc-600 shadow-[0_1px_2px_rgba(0,0,0,0.02)] backdrop-blur-sm">
            Legal
          </span>
          <h1 className="mt-8 text-4xl font-semibold tracking-tight text-zinc-900 sm:text-5xl">
            Privacy Policy
          </h1>
          <p className="mt-4 text-sm text-zinc-500">
            <strong>Last updated:</strong> {LAST_UPDATED}
          </p>

          <div className="prose prose-zinc mt-12 max-w-none text-zinc-600">
            <h2 className="text-zinc-900">What we collect</h2>
            <p>We collect your email address, usage data, and report topics.</p>

            <h2 className="text-zinc-900">How we use it</h2>
            <p>
              We use this information to provide the service, run report generation, and improve output
              quality and reliability.
            </p>

            <h2 className="text-zinc-900">What we do not do</h2>
            <p>We do not sell your data, and we do not train models on your report content.</p>

            <h2 className="text-zinc-900">Data retention</h2>
            <p>Reports are kept for 90 days after account deletion and then permanently removed.</p>

            <h2 className="text-zinc-900">Contact</h2>
            <p>Questions about privacy can be sent to privacy@yourdomain.com.</p>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
