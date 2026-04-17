import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { toast } from "sonner";

import GeneratePage from "@/app/(dashboard)/generate/page";
import { AgentStatusBar } from "@/components/generate/AgentStatusBar";
import { StreamViewer } from "@/components/generate/StreamViewer";
import { TopicForm } from "@/components/generate/TopicForm";
import { useSSEStream } from "@/hooks/useSSEStream";
import { useSession } from "@/hooks/useSession";
import { jobsApi, reportsApi } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { useJobsStore } from "@/store/jobsStore";
import type { FinalReport, JobStatus } from "@/types/jobs";

jest.mock("@/hooks/useSession", () => ({
  useSession: jest.fn(),
}));

jest.mock("@/hooks/useSSEStream", () => ({
  useSSEStream: jest.fn(),
}));

jest.mock("sonner", () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

jest.mock("react-markdown", () => ({
  __esModule: true,
  default: ({ children }: { children: string }) => children,
}));

const mockedUseSession = useSession as jest.MockedFunction<typeof useSession>;
const mockedUseSSEStream = useSSEStream as jest.MockedFunction<
  typeof useSSEStream
>;
const mockedToast = toast as jest.Mocked<typeof toast>;

const mockUser = {
  id: "user-1",
  email: "ali@example.com",
  full_name: "Ali Haider",
  tier: "pro" as const,
  credits: 5,
};

const defaultJobStatus: JobStatus = {
  job_id: "job-1",
  status: "queued",
  agent_stage: "queued",
  progress_pct: 0,
};

const finalReport: FinalReport = {
  topic: "The future of renewable energy",
  report_type: "analytical",
  executive_summary: "A concise summary.",
  markdown_output: "# Report\n\n## Findings\nClean energy is scaling fast.",
  total_word_count: 620,
  quality_score: 0.91,
  qa_passed: true,
  all_citations: [
    {
      index: 1,
      url: "https://example.com/report",
      title: "Energy Outlook",
      inline_reference: "[1] Energy Outlook — https://example.com/report",
    },
  ],
  timestamp: "2026-04-17T12:00:00.000Z",
};

describe("generate flow", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useJobsStore.getState().reset();
    useAuthStore.setState({
      user: mockUser,
      token: "token-123",
      isLoading: false,
      isAuthenticated: true,
    });
    mockedUseSession.mockReturnValue({
      user: mockUser,
      token: "token-123",
      isLoading: false,
      isAuthenticated: true,
      logout: jest.fn(),
    });
    mockedUseSSEStream.mockReturnValue({
      streamedText: "",
      currentStage: "queued",
      isStreaming: false,
      isComplete: false,
      reportId: null,
      error: null,
    });
    jest.spyOn(jobsApi, "create").mockResolvedValue({
      job_id: "job-1",
      status: "queued",
      credits_deducted: 1,
    });
    jest.spyOn(jobsApi, "getStatus").mockResolvedValue(defaultJobStatus);
    jest.spyOn(reportsApi, "get").mockResolvedValue(finalReport);
  });

  afterEach(() => {
    cleanup();
    useJobsStore.getState().reset();
    jest.restoreAllMocks();
  });

  it("test_topic_form_renders", () => {
    render(
      <TopicForm
        creditsRemaining={3}
        isLoading={false}
        onSubmit={jest.fn()}
      />,
    );

    expect(screen.getByLabelText(/topic/i)).toBeInTheDocument();
    expect(screen.getByText("Analytical")).toBeInTheDocument();
    expect(screen.getByText("Informational")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /generate report/i }),
    ).toBeInTheDocument();
  });

  it("test_topic_form_validation", async () => {
    render(
      <TopicForm
        creditsRemaining={3}
        isLoading={false}
        onSubmit={jest.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText(/topic/i), {
      target: { value: "short" },
    });
    fireEvent.click(screen.getByRole("button", { name: /generate report/i }));

    expect(
      await screen.findByText("Topic must be at least 10 characters."),
    ).toBeInTheDocument();
  });

  it("test_no_credits_disables_button", () => {
    render(
      <TopicForm
        creditsRemaining={0}
        isLoading={false}
        onSubmit={jest.fn()}
      />,
    );

    expect(
      screen.getByRole("button", { name: /generate report/i }),
    ).toBeDisabled();
    expect(screen.getByText("No credits remaining")).toBeInTheDocument();
  });

  it("test_agent_status_bar_stages", () => {
    render(<AgentStatusBar currentStage="planning" progress_pct={35} />);

    expect(screen.getByTestId("agent-researcher-status")).toHaveTextContent(
      "complete",
    );
    expect(screen.getByTestId("agent-planner-status")).toHaveTextContent(
      "active",
    );
    expect(screen.getByTestId("agent-writer-status")).toHaveTextContent(
      "waiting",
    );
    expect(screen.getByTestId("agent-qa-status")).toHaveTextContent("waiting");
  });

  it("test_stream_viewer_autoscroll", () => {
    const scrollSpy = jest.spyOn(Element.prototype, "scrollIntoView");
    const { rerender } = render(
      <StreamViewer
        isComplete={false}
        isStreaming={true}
        streamedText="## First draft"
      />,
    );

    scrollSpy.mockClear();

    rerender(
      <StreamViewer
        isComplete={false}
        isStreaming={true}
        streamedText="## First draft\n\nMore text"
      />,
    );

    expect(scrollSpy).toHaveBeenCalled();
  });

  it("test_generate_page_submit", async () => {
    render(<GeneratePage />);

    fireEvent.change(screen.getByLabelText(/topic/i), {
      target: { value: "The future of renewable energy in Southeast Asia" },
    });
    fireEvent.click(screen.getByRole("button", { name: /generate report/i }));

    await waitFor(() => {
      expect(jobsApi.create).toHaveBeenCalledWith(
        "The future of renewable energy in Southeast Asia",
        "analytical",
      );
    });

    expect(await screen.findByText(/job queued/i)).toBeInTheDocument();
  });

  it("test_generate_page_complete", async () => {
    mockedUseSSEStream.mockReturnValue({
      streamedText: "# Report\n\n## Findings\nClean energy is scaling fast.",
      currentStage: "complete",
      isStreaming: false,
      isComplete: true,
      reportId: "report-1",
      error: null,
    });
    jest.spyOn(jobsApi, "getStatus").mockResolvedValue({
      ...defaultJobStatus,
      status: "writing",
      agent_stage: "writing",
      progress_pct: 72,
    });

    render(<GeneratePage />);

    fireEvent.change(screen.getByLabelText(/topic/i), {
      target: { value: "The future of renewable energy in Southeast Asia" },
    });
    fireEvent.click(screen.getByRole("button", { name: /generate report/i }));

    await waitFor(() => {
      expect(reportsApi.get).toHaveBeenCalledWith("report-1");
    });

    expect(
      await screen.findByRole("link", { name: /download pdf/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /copy markdown/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /new report/i }),
    ).toBeInTheDocument();
  });

  it("test_generate_page_failed", async () => {
    mockedUseSSEStream.mockReturnValue({
      streamedText: "Partial draft",
      currentStage: "writing",
      isStreaming: false,
      isComplete: false,
      reportId: null,
      error: "Pipeline failed",
    });
    jest.spyOn(jobsApi, "getStatus").mockResolvedValue({
      ...defaultJobStatus,
      status: "writing",
      agent_stage: "writing",
      progress_pct: 54,
    });

    render(<GeneratePage />);

    fireEvent.change(screen.getByLabelText(/topic/i), {
      target: { value: "The future of renewable energy in Southeast Asia" },
    });
    fireEvent.click(screen.getByRole("button", { name: /generate report/i }));

    expect(
      await screen.findByText("We hit a snag while generating your report"),
    ).toBeInTheDocument();
    expect(screen.getByText("Pipeline failed")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /try again/i }),
    ).toBeInTheDocument();
    expect(mockedToast.error).toHaveBeenCalledWith("Pipeline failed");
  });
});
