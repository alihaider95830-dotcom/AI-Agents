import Link from "next/link";

export default function CtaSection(): JSX.Element {
  return (
    <section className="bg-indigo-600 px-4 py-16 sm:px-6">
      <div className="mx-auto w-full max-w-4xl text-center">
        <h2 className="text-3xl font-semibold text-white sm:text-4xl">Start generating in 30 seconds.</h2>
        <p className="mt-3 text-lg text-indigo-200">No credit card. No setup. Just paste a topic and go.</p>

        <Link
          href="/auth/signup"
          className="mt-8 inline-flex items-center justify-center rounded-xl bg-white px-8 py-4 text-lg font-medium text-indigo-700 transition hover:bg-indigo-50"
        >
          Generate your first report -&gt;
        </Link>
      </div>
    </section>
  );
}
