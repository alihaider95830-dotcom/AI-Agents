import type { Metadata } from "next";
import dynamic from "next/dynamic";

import HeroSection from "@/components/landing/HeroSection";
import NavBar from "@/components/landing/NavBar";
import SocialProofBar from "@/components/landing/SocialProofBar";
import CtaSection from "@/components/landing/CtaSection";
import Footer from "@/components/landing/Footer";

const HowItWorksSection = dynamic(
  () => import("@/components/landing/HowItWorksSection"),
  { loading: () => <div className="h-96 animate-pulse bg-neutral-50" /> },
);

const FeaturesSection = dynamic(
  () => import("@/components/landing/FeaturesSection"),
  { loading: () => <div className="h-96 animate-pulse bg-neutral-50" /> },
);

const ExampleReportSection = dynamic(
  () => import("@/components/landing/ExampleReportSection"),
  { loading: () => <div className="h-96 animate-pulse bg-neutral-50" /> },
);

const PricingSection = dynamic(
  () => import("@/components/landing/PricingSection"),
  { loading: () => <div className="h-96 animate-pulse bg-neutral-50" /> },
);

const FaqSection = dynamic(
  () => import("@/components/landing/FaqSection"),
  { loading: () => <div className="h-96 animate-pulse bg-neutral-50" /> },
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
    <main className="bg-white text-neutral-900">
      <NavBar />
      <HeroSection />
      <SocialProofBar />
      <HowItWorksSection />
      <FeaturesSection />
      <ExampleReportSection />
      <PricingSection />
      <FaqSection />
      <CtaSection />
      <Footer />
    </main>
  );
}
