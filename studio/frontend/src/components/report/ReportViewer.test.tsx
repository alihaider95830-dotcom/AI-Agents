import { fireEvent, render, screen } from "@testing-library/react";

import { ReportViewer } from "@/components/report/ReportViewer";
import { useSupabaseAccessToken } from "@/hooks/useSupabaseAccessToken";
import type { Report } from "@/lib/api/reports";

const mockPush = jest.fn();
const mockRefresh = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    refresh: mockRefresh,
  }),
}));

jest.mock("@/hooks/useSupabaseAccessToken", () => ({
  useSupabaseAccessToken: jest.fn(),
}));

jest.mock("sonner", () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

jest.mock("remark-gfm", () => jest.fn());
jest.mock("rehype-highlight", () => jest.fn());

jest.mock("react-markdown", () => ({
  __esModule: true,
  default: ({ children }: { children: string }) => {
    const lines = children.split("\n");
    return (
      <div>
        {lines.map((line) => {
          if (line.startsWith("# ")) {
            return <h1 key={line}>{line.replace("# ", "")}</h1>;
          }
          return line ? <p key={line}>{line}</p> : null;
        })}
      </div>
    );
  },
}));

const mockedUseSupabaseAccessToken =
  useSupabaseAccessToken as jest.MockedFunction<typeof useSupabaseAccessToken>;

const baseReport: Report = {
  id: "report-1",
  title: "A useful report",
  topic: "A useful report topic",
  report_type: "market_analysis",
  status: "done",
  content_md: "# Hello\nWorld",
  word_count: 120,
  created_at: "2025-04-20T12:00:00.000Z",
  completed_at: "2025-04-20T12:05:00.000Z",
};

describe("ReportViewer", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedUseSupabaseAccessToken.mockReturnValue({
      isLoading: false,
      token: "token-123",
    });
  });

  it("test_renders_done_report_with_markdown", () => {
    render(<ReportViewer report={baseReport} />);

    expect(
      screen.getByRole("heading", { name: "Hello" }),
    ).toBeInTheDocument();
    expect(screen.getByText("World")).toBeInTheDocument();
  });

  it("test_renders_skeleton_when_pending", () => {
    render(
      <ReportViewer
        report={{
          ...baseReport,
          status: "pending",
          content_md: "# Hidden",
        }}
      />,
    );

    expect(screen.getByTestId("report-skeleton")).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Hidden" }),
    ).not.toBeInTheDocument();
  });

  it("test_renders_failed_state", () => {
    render(
      <ReportViewer
        report={{
          ...baseReport,
          status: "failed",
          content_md: null,
        }}
      />,
    );

    expect(screen.getByText(/Report generation failed/i)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /try again/i }),
    ).toBeInTheDocument();
  });

  it("test_copy_button_calls_clipboard", () => {
    const writeText = jest.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: {
        writeText,
      },
    });

    render(<ReportViewer report={baseReport} />);
    fireEvent.click(
      screen.getByRole("button", { name: /copy markdown/i }),
    );

    expect(writeText).toHaveBeenCalledWith(baseReport.content_md);
  });

  it("test_delete_shows_confirmation_dialog", async () => {
    render(<ReportViewer report={baseReport} />);

    fireEvent.click(screen.getByRole("button", { name: /^delete$/i }));

    expect(
      await screen.findByText("Delete this report?"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/This removes the report from your history/i),
    ).toBeInTheDocument();
  });

  it("test_back_to_top_hidden_initially", () => {
    render(<ReportViewer report={baseReport} />);

    expect(
      screen.queryByRole("button", { name: /back to top/i }),
    ).not.toBeInTheDocument();
  });
});
