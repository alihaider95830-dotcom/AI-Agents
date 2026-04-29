import { LayoutList, PenLine, Search, ShieldCheck } from "lucide-react";

const steps = [
  {
    icon: Search,
    name: "Researcher",
    description:
      "Searches 8-12 live sources and indexes key facts, statistics, and competitor mentions.",
  },
  {
    icon: LayoutList,
    name: "Planner",
    description:
      "Reads the research and builds a structured outline with arguments for each section.",
  },
  {
    icon: PenLine,
    name: "Writer",
    description:
      "Drafts the full report with inline citations, professional tone, and clean markdown formatting.",
  },
  {
    icon: ShieldCheck,
    name: "QA Specialist",
    description:
      "Cross-references every claim against the source list, fixes inconsistencies, and polishes the final copy.",
  },
];

export default function HowItWorksSection(): JSX.Element {
  return (
    <section className="px-4 py-16 sm:px-6" aria-labelledby="how-it-works-heading">
      <div className="mx-auto w-full max-w-6xl">
        <div className="text-center">
          <h2 id="how-it-works-heading" className="text-3xl font-semibold text-neutral-900">
            How it works
          </h2>
          <p className="mt-2 text-neutral-600">Four agents. One polished report.</p>
        </div>

        <div className="mt-12 grid gap-8 md:grid-cols-4 md:gap-6">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <article key={step.name} className="relative pl-10 md:pl-0">
                {index < steps.length - 1 ? (
                  <>
                    <div className="absolute left-[15px] top-9 h-full w-px bg-neutral-200 md:hidden" aria-hidden="true" />
                    <div className="absolute left-[calc(50%+1.5rem)] top-4 hidden h-px w-[calc(100%-3rem)] bg-neutral-200 md:block" aria-hidden="true" />
                  </>
                ) : null}

                <div className="absolute left-0 top-0 flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 text-sm font-semibold text-white md:relative md:mx-auto md:mb-4">
                  {index + 1}
                </div>

                <div className="rounded-xl border border-neutral-200 bg-white p-5 md:text-center">
                  <Icon className="h-5 w-5 text-indigo-600 md:mx-auto" aria-hidden="true" />
                  <h3 className="mt-3 text-lg font-semibold text-neutral-900">{step.name}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-neutral-600">{step.description}</p>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
