import { Database, FileText, Globe, Lock, RefreshCw, Zap } from "lucide-react";

const features = [
  {
    icon: Globe,
    title: "Live web research",
    description: "Agents search the live web - no stale training data.",
  },
  {
    icon: Database,
    title: "Vector knowledge base",
    description: "Research is embedded and indexed so every claim is traceable.",
  },
  {
    icon: FileText,
    title: "PDF + Markdown export",
    description: "Download your report as a beautifully formatted PDF or raw markdown.",
  },
  {
    icon: Zap,
    title: "Under 90 seconds",
    description: "The full pipeline - research to final copy - completes in under 90 seconds.",
  },
  {
    icon: RefreshCw,
    title: "Fact-checked output",
    description: "A dedicated QA agent cross-references every claim before you see it.",
  },
  {
    icon: Lock,
    title: "Your data stays yours",
    description: "Reports are private to your account. We never train on your content.",
  },
];

export default function FeaturesSection(): JSX.Element {
  return (
    <section id="features" className="px-4 py-16 sm:px-6" aria-labelledby="features-heading">
      <div className="mx-auto w-full max-w-6xl">
        <div className="text-center">
          <h2 id="features-heading" className="text-3xl font-semibold text-neutral-900">
            Everything you need. Nothing you don&apos;t.
          </h2>
        </div>

        <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <article
                key={feature.title}
                className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm transition hover:shadow-md"
              >
                <Icon className="h-6 w-6 text-indigo-600" aria-hidden="true" />
                <h3 className="mt-4 text-lg font-semibold text-neutral-900">{feature.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-neutral-600">{feature.description}</p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
