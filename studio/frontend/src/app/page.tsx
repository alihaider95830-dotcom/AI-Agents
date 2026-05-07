import type { Metadata } from "next";
import dynamic from "next/dynamic";

import HeroSection from "@/components/landing/HeroSection";
import NavBar from "@/components/landing/NavBar";
import SocialProofBar from "@/components/landing/SocialProofBar";
import CtaSection from "@/components/landing/CtaSection";
import Footer from "@/components/landing/Footer";

const HowItWorksSection = dynamic(
  () => import("@/components/landing/HowItWorksSection"),
  { loading: () => <div className="h-96 animate-pulse bg-white/05 rounded-[2rem]" /> },
);

const FeaturesSection = dynamic(
  () => import("@/components/landing/FeaturesSection"),
  { loading: () => <div className="h-96 animate-pulse bg-white/05 rounded-[2rem]" /> },
);

const ExampleReportSection = dynamic(
  () => import("@/components/landing/ExampleReportSection"),
  { loading: () => <div className="h-96 animate-pulse bg-white/05 rounded-[2rem]" /> },
);

const PricingSection = dynamic(
  () => import("@/components/landing/PricingSection"),
  { loading: () => <div className="h-96 animate-pulse bg-white/05 rounded-[2rem]" /> },
);

const FaqSection = dynamic(
  () => import("@/components/landing/FaqSection"),
  { loading: () => <div className="h-96 animate-pulse bg-white/05 rounded-[2rem]" /> },
);

export const metadata: Metadata = {
  title: "Studio - AI Market Research Reports in Minutes",
  description:
    "Studio uses a team of AI agents to research, plan, write, and fact-check professional market research reports automatically. Get your first report free.",
  openGraph: {
    title: "Studio - AI Market Research Reports in Minutes",
    description:
      "Research, planned, written, and fact-checked by AI agents. Professional reports in under 90 seconds.",
    url: "https://yourdomain.com",
    siteName: "Studio",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Studio - AI Market Research Reports in Minutes",
    description: "AI agents that research, plan, write and fact-check reports for you.",
  },
};

export default function HomePage(): JSX.Element {
  return (
    <main className="text-[var(--text-primary)]">
      <NavBar />
      
      {/* Hero Section - Increased padding */}
      <div className="bg-gradient-to-b from-white/0 to-white/0">
        <div className="py-12 sm:py-20 lg:py-24">
          <HeroSection />
        </div>
      </div>
      
      <div className="mx-auto max-w-6xl px-6">
        <hr className="border-white/[0.1]" />
      </div>

      
      {/* Social Proof - Light background */}
      <div className="bg-white/[0.02] py-16 sm:py-20 md:py-24">
        <SocialProofBar />
      </div>
      
      <div className="mx-auto max-w-6xl px-6">
        <hr className="border-white/[0.1]" />
      </div>

      
      {/* How It Works - No background */}
      <div className="py-20 sm:py-24 md:py-32">
        <HowItWorksSection />
      </div>
      
      <div className="mx-auto max-w-6xl px-6">
        <hr className="border-white/[0.1]" />
      </div>

      
      {/* Features - Light background */}
      <div className="bg-white/[0.015] py-20 sm:py-24 md:py-32">
        <FeaturesSection />
      </div>
      
      <div className="mx-auto max-w-6xl px-6">
        <hr className="border-white/[0.1]" />
      </div>

      
      {/* Example Report - No background */}
      <div className="py-20 sm:py-24 md:py-32">
        <ExampleReportSection />
      </div>
      
      <div className="mx-auto max-w-6xl px-6">
        <hr className="border-white/[0.1]" />
      </div>

      
      {/* Pricing - Light background */}
      <div className="bg-white/[0.02] py-20 sm:py-24 md:py-32">
        <PricingSection />
      </div>
      
      <div className="mx-auto max-w-6xl px-6">
        <hr className="border-white/[0.1]" />
      </div>

      
      {/* FAQ - No background */}
      <div className="py-20 sm:py-24 md:py-32">
        <FaqSection />
      </div>
      
      <CtaSection />
      <Footer />
    </main>
  );
}

