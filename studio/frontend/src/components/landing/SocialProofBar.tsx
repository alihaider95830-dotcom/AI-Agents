const stats = [
  { value: "500+", label: "reports generated" },
  { value: "12", label: "sources per report" },
  { value: "< 90 sec", label: "avg. generation" },
  { value: "4", label: "AI agents per report" },
];

export default function SocialProofBar(): JSX.Element {
  return (
    <section className="border-y border-neutral-100 bg-neutral-50 px-4 py-6 sm:px-6">
      <div className="mx-auto grid w-full max-w-6xl grid-cols-2 gap-4 md:grid-cols-4 md:divide-x md:divide-neutral-200 md:gap-0">
        {stats.map((stat) => (
          <div key={stat.label} className="text-center md:px-6">
            <p className="text-2xl font-bold text-neutral-900">{stat.value}</p>
            <p className="mt-1 text-sm text-neutral-500">{stat.label}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
