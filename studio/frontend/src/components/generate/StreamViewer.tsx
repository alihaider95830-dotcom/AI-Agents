"use client";

import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";

import { Badge } from "@/components/ui/Badge";

interface StreamViewerProps {
  streamedText: string;
  isStreaming: boolean;
  isComplete: boolean;
}

export const StreamViewer = ({
  streamedText,
  isStreaming,
  isComplete,
}: StreamViewerProps): JSX.Element => {
  const bottomMarkerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomMarkerRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [streamedText, isComplete]);

  const hasContent = streamedText.trim().length > 0;

  return (
    <section className="rounded-[1.75rem] border border-slate-200/70 bg-white/85 p-5 shadow-panel transition-all duration-300 dark:border-slate-800 dark:bg-slate-950/80">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-brand-ocean dark:text-brand-gold">
            Live draft
          </p>
          <h2 className="mt-2 font-[var(--font-heading)] text-2xl font-semibold text-slate-900 dark:text-white">
            Streaming report output
          </h2>
        </div>
        {isComplete ? <Badge>Report complete ✓</Badge> : null}
      </div>

      <div className="mt-6 max-h-[70vh] overflow-y-auto rounded-[1.5rem] border border-slate-200/80 bg-brand-sand/50 p-5 dark:border-slate-800 dark:bg-slate-950/70">
        {!hasContent ? (
          <div className="space-y-4" data-testid="stream-skeleton">
            <div className="h-4 w-full animate-pulse rounded-full bg-slate-200 dark:bg-slate-800" />
            <div className="h-4 w-3/4 animate-pulse rounded-full bg-slate-200 dark:bg-slate-800" />
            <div className="h-4 w-5/6 animate-pulse rounded-full bg-slate-200 dark:bg-slate-800" />
          </div>
        ) : (
          <div className="prose prose-slate prose-report max-w-none dark:prose-invert">
            <ReactMarkdown>{streamedText}</ReactMarkdown>
            {isStreaming ? (
              <span
                aria-label="Streaming cursor"
                className="inline-block h-5 w-0.5 animate-pulse bg-brand-ocean align-middle dark:bg-brand-gold"
              />
            ) : null}
          </div>
        )}
        <div ref={bottomMarkerRef} />
      </div>
    </section>
  );
};
