"use client";

import { useEffect, useState } from "react";

import { env } from "@/lib/env";

interface TokenEventPayload {
  text: string;
}

interface StageEventPayload {
  stage: string;
}

interface CompleteEventPayload {
  report_id: string;
}

interface ErrorEventPayload {
  message: string;
}

interface SSEStreamState {
  streamedText: string;
  currentStage: string;
  isStreaming: boolean;
  isComplete: boolean;
  reportId: string | null;
  error: string | null;
}

const parseEventData = <T,>(data: string): T | null => {
  try {
    return JSON.parse(data) as T;
  } catch {
    return null;
  }
};

export const useSSEStream = (
  job_id: string | null,
  token: string | null,
): SSEStreamState => {
  const [streamedText, setStreamedText] = useState("");
  const [currentStage, setCurrentStage] = useState("queued");
  const [isStreaming, setIsStreaming] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [reportId, setReportId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!job_id || !token) {
      setStreamedText("");
      setCurrentStage("queued");
      setIsStreaming(false);
      setIsComplete(false);
      setReportId(null);
      setError(null);
      return;
    }

    setStreamedText("");
    setCurrentStage("queued");
    setIsStreaming(true);
    setIsComplete(false);
    setReportId(null);
    setError(null);

    const streamUrl = new URL(`/stream/${job_id}`, env.NEXT_PUBLIC_API_URL);
    streamUrl.searchParams.set("token", token);

    const eventSource = new EventSource(streamUrl.toString());

    eventSource.addEventListener("token", (event: Event) => {
      const parsedEvent = parseEventData<TokenEventPayload>(
        (event as MessageEvent<string>).data,
      );

      if (!parsedEvent?.text) {
        return;
      }

      setStreamedText((currentText) => currentText + parsedEvent.text);
    });

    eventSource.addEventListener("stage", (event: Event) => {
      const parsedEvent = parseEventData<StageEventPayload>(
        (event as MessageEvent<string>).data,
      );

      if (!parsedEvent?.stage) {
        return;
      }

      setCurrentStage(parsedEvent.stage);
    });

    eventSource.addEventListener("complete", (event: Event) => {
      const parsedEvent = parseEventData<CompleteEventPayload>(
        (event as MessageEvent<string>).data,
      );

      setCurrentStage("complete");
      setIsStreaming(false);
      setIsComplete(true);
      setReportId(parsedEvent?.report_id ?? null);
      eventSource.close();
    });

    eventSource.addEventListener("error", (event: Event) => {
      const parsedEvent =
        "data" in event
          ? parseEventData<ErrorEventPayload>(
              (event as MessageEvent<string>).data,
            )
          : null;

      setError(parsedEvent?.message ?? "The report stream disconnected.");
      setIsStreaming(false);
      eventSource.close();
    });

    return () => {
      eventSource.close();
      setIsStreaming(false);
    };
  }, [job_id, token]);

  return {
    streamedText,
    currentStage,
    isStreaming,
    isComplete,
    reportId,
    error,
  };
};
