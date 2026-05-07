import type { Metadata } from "next";
import { DM_Sans, DM_Mono } from "next/font/google";

import "@/app/globals.css";
import { Providers } from "@/components/providers/Providers";

const dmSans = DM_Sans({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-sans",
});

const dmMono = DM_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  display: "swap",
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "Report Forge",
  description: "AI-powered report generation workspace",
};

interface RootLayoutProps {
  children: React.ReactNode;
}

export default function RootLayout({
  children,
}: RootLayoutProps): JSX.Element {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${dmSans.variable} ${dmMono.variable} font-sans bg-noise`}>
        <div className="bg-mesh" />
        <div className="orb-1" />
        <div className="orb-2" />
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
