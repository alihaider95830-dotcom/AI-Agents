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
    <section className="glass-card p-8 bg-white/[0.02] border-white/[0.05] relative overflow-hidden glass-scanline">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between relative z-10">
        <div>
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/05 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.15em] text-[var(--text-secondary)] backdrop-blur-sm">
            LIVE_DRAFT_BUFFER
          </span>
          <h2 className="mt-6 text-[22px] font-semibold tracking-tight text-white">
            Synthetic Report Stream
          </h2>
        </div>
        {isComplete ? (
          <div className="flex items-center gap-2.5 rounded-full bg-white px-5 py-2 text-[11px] font-bold uppercase tracking-[0.1em] text-[var(--text-inverse)] shadow-[0_0_20px_rgba(255,255,255,0.3)]">
            <span>READY_FOR_EXPORT</span>
            <span>✓</span>
          </div>
        ) : isStreaming ? (
          <div className="flex items-center gap-2.5 rounded-full border border-white/10 bg-white/05 px-5 py-2 text-[11px] font-bold uppercase tracking-[0.1em] text-white animate-pulse">
            <span className="h-1.5 w-1.5 rounded-full bg-white shadow-[0_0_8px_white]" />
            INCOMING_DATA
          </div>
        ) : null}
      </div>

      <div className="mt-8 max-h-[70vh] overflow-y-auto rounded-[var(--radius-xl)] border border-white/05 bg-black/40 p-8 sm:p-12 custom-scrollbar relative z-10 shadow-[inset_0_2px_20px_rgba(0,0,0,0.4)]">
        {!hasContent ? (
          <div className="space-y-8" data-testid="stream-skeleton">
            <div className="h-5 w-1/3 animate-pulse rounded-md bg-white/10" />
            <div className="space-y-4">
              <div className="h-3 w-full animate-pulse rounded-full bg-white/05" />
              <div className="h-3 w-[95%] animate-pulse rounded-full bg-white/05" />
              <div className="h-3 w-[90%] animate-pulse rounded-full bg-white/05" />
            </div>
            <div className="h-3 w-[40%] animate-pulse rounded-full bg-white/05" />
            <div className="space-y-4 pt-4">
              <div className="h-3 w-full animate-pulse rounded-full bg-white/05" />
              <div className="h-3 w-[85%] animate-pulse rounded-full bg-white/05" />
            </div>
          </div>
        ) : (
          <div className="prose prose-zinc prose-report max-w-none dark:prose-invert">
            <ReactMarkdown>{streamedText}</ReactMarkdown>
            {isStreaming ? (
              <span
                aria-label="Streaming cursor"
                className="ml-1 inline-block h-5 w-1.5 animate-pulse rounded-full bg-white align-middle shadow-[0_0_12px_rgba(255,255,255,0.8)]"
              />
            ) : null}
          </div>
        )}
        <div ref={bottomMarkerRef} />
      </div>
    </section>
  );
};
