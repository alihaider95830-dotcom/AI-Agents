import Image from "next/image";
import Link from "next/link";

const HERO_SVG = encodeURIComponent(`
<svg xmlns='http://www.w3.org/2000/svg' width='1280' height='820' viewBox='0 0 1280 820' fill='none'>
  <defs>
    <linearGradient id='bg' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0%' stop-color='#f5f5f5'/>
      <stop offset='100%' stop-color='#e5e7eb'/>
    </linearGradient>
  </defs>
  <rect x='20' y='20' width='1240' height='780' rx='24' fill='url(#bg)' stroke='#d1d5db'/>
  <rect x='20' y='20' width='1240' height='74' rx='24' fill='#f3f4f6'/>
  <circle cx='64' cy='57' r='8' fill='#ef4444'/>
  <circle cx='92' cy='57' r='8' fill='#f59e0b'/>
  <circle cx='120' cy='57' r='8' fill='#22c55e'/>
  <rect x='180' y='40' width='420' height='34' rx='17' fill='#ffffff' stroke='#d4d4d8'/>
  <text x='202' y='61' fill='#525252' font-size='14' font-family='Inter, sans-serif'>app.studio.ai/generate</text>

  <rect x='72' y='130' width='1136' height='82' rx='14' fill='#ffffff' stroke='#e5e7eb'/>
  <text x='100' y='163' fill='#737373' font-size='14' font-family='Inter, sans-serif'>Topic</text>
  <text x='100' y='191' fill='#111827' font-size='22' font-family='Inter, sans-serif'>The future of on-device AI</text>

  <rect x='72' y='236' width='250' height='62' rx='14' fill='#ecfdf3' stroke='#bbf7d0'/>
  <text x='94' y='261' fill='#166534' font-size='14' font-family='Inter, sans-serif'>Researcher</text>
  <text x='94' y='282' fill='#15803d' font-size='15' font-family='Inter, sans-serif'>Done</text>

  <rect x='336' y='236' width='250' height='62' rx='14' fill='#ecfdf3' stroke='#bbf7d0'/>
  <text x='358' y='261' fill='#166534' font-size='14' font-family='Inter, sans-serif'>Planner</text>
  <text x='358' y='282' fill='#15803d' font-size='15' font-family='Inter, sans-serif'>Done</text>

  <rect x='600' y='236' width='250' height='62' rx='14' fill='#eef2ff' stroke='#c7d2fe'/>
  <text x='622' y='261' fill='#3730a3' font-size='14' font-family='Inter, sans-serif'>Writer</text>
  <text x='622' y='282' fill='#4338ca' font-size='15' font-family='Inter, sans-serif'>Writing...</text>
  <circle cx='808' cy='269' r='7' fill='#4f46e5'>
    <animate attributeName='opacity' values='1;0.35;1' dur='1.2s' repeatCount='indefinite'/>
  </circle>

  <rect x='864' y='236' width='250' height='62' rx='14' fill='#f5f5f5' stroke='#e5e7eb'/>
  <text x='886' y='261' fill='#525252' font-size='14' font-family='Inter, sans-serif'>QA</text>
  <text x='886' y='282' fill='#6b7280' font-size='15' font-family='Inter, sans-serif'>Waiting</text>

  <rect x='72' y='326' width='1136' height='420' rx='18' fill='#ffffff' stroke='#e5e7eb'/>
  <text x='102' y='368' fill='#111827' font-size='26' font-family='Inter, sans-serif' font-weight='600'>On-Device AI Market Overview</text>
  <text x='102' y='406' fill='#374151' font-size='17' font-family='Inter, sans-serif'>On-device AI is moving from experimental features into mainstream products.</text>
  <text x='102' y='434' fill='#374151' font-size='17' font-family='Inter, sans-serif'>Falling model sizes and better NPUs are accelerating adoption across mobile and edge devices.</text>
</svg>
`);

const HERO_SRC = `data:image/svg+xml;charset=utf-8,${HERO_SVG}`;

export default function HeroSection(): JSX.Element {
  return (
    <section className="px-4 pb-12 pt-12 sm:px-6 lg:pb-16 lg:pt-20">
      <div className="mx-auto flex w-full max-w-6xl flex-col items-center">
        <div className="mx-auto flex min-h-[calc(100vh-5rem)] w-full max-w-4xl flex-col items-center text-center max-lg:min-h-0">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-neutral-200 px-3 py-1 text-sm text-neutral-500">
            <span aria-hidden="true">✦</span>
            AI-powered research &amp; writing
          </span>

          <h1 className="mt-6 text-3xl font-bold leading-tight tracking-tight text-neutral-900 sm:text-5xl">
            Market research reports, <span className="text-indigo-600">written by AI</span> in minutes.
          </h1>

          <p className="mt-5 max-w-2xl text-base leading-relaxed text-neutral-600 sm:text-lg">
            Give Studio a topic. A team of AI agents researches the web, builds a strategy, writes the
            report, and fact-checks every claim - automatically. You get a polished PDF in under 90
            seconds.
          </p>

          <div className="mt-8 flex w-full flex-col items-center justify-center gap-3 sm:w-auto sm:flex-row">
            <Link
              href="/auth/signup"
              className="inline-flex w-full items-center justify-center rounded-lg bg-indigo-600 px-6 py-3 text-base font-medium text-white transition hover:bg-indigo-700 sm:w-auto"
            >
              Generate your first report -&gt;
            </Link>
            <Link
              href="#example-report"
              className="inline-flex w-full items-center justify-center rounded-lg border border-neutral-300 px-6 py-3 text-base font-medium text-neutral-700 transition hover:bg-neutral-50 sm:w-auto"
            >
              See a sample report
            </Link>
          </div>

          <p className="mt-4 text-sm text-neutral-500">
            Free forever · No credit card required · 2 reports per month
          </p>
        </div>

        <div className="mt-8 w-full max-w-6xl [transform:perspective(1000px)_rotateX(5deg)]">
          <Image
            src={HERO_SRC}
            alt="Studio report generation dashboard preview"
            width={1280}
            height={820}
            priority
            className="h-auto w-full rounded-2xl shadow-2xl"
          />
        </div>
      </div>
    </section>
  );
}
