import Image from "next/image";
import Link from "next/link";
import { Star } from "lucide-react";
import { Button } from "@/components/ui/Button";

const HERO_SVG = encodeURIComponent(`
<svg xmlns='http://www.w3.org/2000/svg' width='1280' height='820' viewBox='0 0 1280 820' fill='none'>
  <defs>
    <linearGradient id='bg' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0%' stop-color='#0a0a0b'/>
      <stop offset='100%' stop-color='#111113'/>
    </linearGradient>
    <pattern id='grid' width='60' height='60' patternUnits='userSpaceOnUse'>
      <path d='M0 60L60 60 M60 0L60 60' fill='none' stroke='#ffffff' stroke-opacity='0.03' stroke-width='0.5'/>
    </pattern>
  </defs>
  
  <rect width='1280' height='820' fill='url(#bg)'/>
  <rect width='1280' height='820' fill='url(#grid)'/>

  <!-- Ambient Orbs -->
  <circle cx='200' cy='100' r='200' fill='white' fill-opacity='0.02' filter='blur(80px)'/>
  <circle cx='1000' cy='600' r='150' fill='white' fill-opacity='0.015' filter='blur(100px)'/>

  <!-- Main App Window Frame -->
  <rect x='40' y='60' width='1200' height='720' rx='24' fill='white' fill-opacity='0.03' stroke='white' stroke-opacity='0.1' stroke-width='1'/>
  
  <!-- Header Bar -->
  <path d='M40 84 a24 24 0 0 1 24 -24 h1152 a24 24 0 0 1 24 24 v36 h-1200 v-36 z' fill='white' fill-opacity='0.02'/>
  <line x1='40' y1='120' x2='1240' y2='120' stroke='white' stroke-opacity='0.05' stroke-width='1'/>
  
  <!-- Mac Dots -->
  <circle cx='80' cy='90' r='6' fill='white' fill-opacity='0.1'/>
  <circle cx='104' cy='90' r='6' fill='white' fill-opacity='0.1'/>
  <circle cx='128' cy='90' r='6' fill='white' fill-opacity='0.1'/>

  <!-- Sidebar -->
  <rect x='40' y='121' width='240' height='659' fill='white' fill-opacity='0.01'/>
  <line x1='280' y1='121' x2='280' y2='780' stroke='white' stroke-opacity='0.05' stroke-width='1'/>
  
  <!-- Sidebar Items -->
  <rect x='56' y='140' width='208' height='36' rx='8' fill='white' fill-opacity='0.05'/>
  <rect x='72' y='152' width='12' height='12' rx='3' fill='white'/>
  <text x='94' y='163' fill='white' font-size='13' font-family='DM Sans, sans-serif' font-weight='500'>Generate</text>

  <rect x='72' y='200' width='12' height='12' rx='3' fill='white' fill-opacity='0.2'/>
  <text x='94' y='209' fill='white' fill-opacity='0.4' font-size='13' font-family='DM Sans, sans-serif'>Reports</text>

  <!-- Main Content Area -->
  <rect x='320' y='160' width='880' height='200' rx='20' fill='white' fill-opacity='0.04' stroke='white' stroke-opacity='0.1' stroke-width='1'/>
  
  <!-- Progress -->
  <rect x='360' y='240' width='800' height='4' rx='2' fill='white' fill-opacity='0.05'/>
  <rect x='360' y='240' width='480' height='4' rx='2' fill='white' fill-opacity='0.6'/>
  
  <!-- Steps -->
  <circle cx='360' cy='242' r='14' fill='white' stroke='white' stroke-opacity='0.2'/>
  <circle cx='360' cy='242' r='4' fill='#0a0a0b'/>
  
  <circle cx='520' cy='242' r='14' fill='white' stroke='white' stroke-opacity='0.2'/>
  <circle cx='520' cy='242' r='4' fill='#0a0a0b'/>

  <circle cx='680' cy='242' r='16' fill='white'/>
  <circle cx='680' cy='242' r='5' fill='#0a0a0b'/>
  <text x='680' y='280' fill='white' font-size='11' font-family='DM Sans, sans-serif' font-weight='600' text-anchor='middle' letter-spacing='0.1em'>WRITING</text>

  <!-- Content Block -->
  <rect x='320' y='400' width='880' height='320' rx='20' fill='white' fill-opacity='0.02' stroke='white' stroke-opacity='0.05' stroke-width='1'/>
  <rect x='360' y='440' width='300' height='20' rx='4' fill='white' fill-opacity='0.05'/>
  <rect x='360' y='480' width='800' height='8' rx='4' fill='white' fill-opacity='0.03'/>
  <rect x='360' y='504' width='760' height='8' rx='4' fill='white' fill-opacity='0.03'/>
  <rect x='360' y='528' width='600' height='8' rx='4' fill='white' fill-opacity='0.03'/>
</svg>
`);

const HERO_SRC = `data:image/svg+xml;charset=utf-8,${HERO_SVG}`;

export default function HeroSection(): JSX.Element {
  return (
    <section className="relative overflow-hidden px-6 pb-24 pt-32 lg:pb-32 lg:pt-48">
      <div className="mx-auto flex w-full max-w-6xl flex-col items-center">
        <div className="mx-auto flex w-full max-w-4xl flex-col items-center text-center animate-glass-enter">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/05 px-4 py-1.5 text-[11px] font-medium uppercase tracking-[0.1em] text-[var(--text-secondary)] backdrop-blur-md">
            <span className="h-1.5 w-1.5 rounded-full bg-white animate-pulse" />
            AI-powered research &amp; writing
          </span>

          <h1 className="mt-12 text-[52px] font-semibold tracking-tight text-white sm:text-[84px] sm:leading-[0.95]">
            Market research reports, <br className="hidden sm:block"/>
            <span className="text-display text-white/30">written by AI</span> in minutes.
          </h1>

          <p className="mt-8 max-w-2xl text-[18px] leading-relaxed text-[var(--text-secondary)] sm:text-[22px] font-light">
            Give Studio a topic. A team of AI agents researches the web, builds a strategy, writes the
            report, and fact-checks every claim — automatically.
          </p>

          <div className="mt-12 flex w-full flex-col items-center justify-center gap-4 sm:w-auto sm:flex-row">
            <Link href="/auth/signup" passHref legacyBehavior>
              <Button 
                size="lg" 
                className="w-full sm:w-auto !rounded-full !h-[64px] px-14 bg-white text-black hover:bg-white/95 shadow-[0_8px_32px_rgba(255,255,255,0.2)] hover:shadow-[0_16px_48px_rgba(255,255,255,0.3)] transition-all duration-300 hover:scale-[1.03] active:scale-[0.98] font-bold text-[16px] sm:text-[17px]"
              >
                Generate your first report
              </Button>
            </Link>
            <Link href="#example-report" passHref legacyBehavior>
              <Button 
                variant="secondary" 
                size="lg" 
                className="w-full sm:w-auto !rounded-full !h-[64px] px-12 border border-white/20 bg-white/[0.05] text-white hover:bg-white/[0.12] hover:border-white/30 shadow-[0_4px_12px_rgba(255,255,255,0.08)] transition-all duration-300 active:scale-[0.98] font-semibold text-[16px] sm:text-[17px]"
              >
                See a sample report
              </Button>
            </Link>
          </div>

          <div className="mt-12 inline-flex items-center gap-2.5 rounded-full border border-emerald-500/40 bg-emerald-500/[0.12] px-6 py-3 backdrop-blur-md hover:border-emerald-500/50 hover:bg-emerald-500/[0.15] transition-all duration-300">
            <Star className="h-5 w-5 text-emerald-400 fill-emerald-400" />
            <p className="text-[15px] sm:text-[16px] font-semibold text-emerald-300 tracking-wide">
              Free forever · No credit card required · 2 reports per month
            </p>
          </div>

        </div>

        <div className="mt-24 w-full max-w-[1200px] relative">
          <div className="absolute -inset-4 rounded-[2rem] bg-white/[0.02] blur-2xl -z-10"></div>
          <div className="glass-card !bg-transparent !p-0 overflow-hidden !rounded-[2rem] shadow-2xl">
            <Image
              src={HERO_SRC}
              alt="Studio report generation dashboard preview"
              width={1280}
              height={820}
              priority
              className="relative h-auto w-full opacity-90"
            />
          </div>
        </div>
      </div>
    </section>
  );
}

