import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { PaymentWarningBanner } from "@/components/billing/PaymentWarningBanner";
import { useSupabaseAccessToken } from "@/hooks/useSupabaseAccessToken";
import {
  createBillingPortal,
  retryPayment,
} from "@/lib/api/billing";
import { ApiError } from "@/lib/api/client";

jest.mock("@/hooks/useSupabaseAccessToken", () => ({
  useSupabaseAccessToken: jest.fn(),
}));

jest.mock("@/lib/api/billing", () => ({
  createBillingPortal: jest.fn(),
  retryPayment: jest.fn(),
}));

const mockedUseSupabaseAccessToken =
  useSupabaseAccessToken as jest.MockedFunction<typeof useSupabaseAccessToken>;
const mockedRetryPayment = retryPayment as jest.MockedFunction<typeof retryPayment>;
const mockedCreateBillingPortal =
  createBillingPortal as jest.MockedFunction<typeof createBillingPortal>;

describe("PaymentWarningBanner", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedUseSupabaseAccessToken.mockReturnValue({
      isLoading: false,
      token: "token-123",
    });
    mockedCreateBillingPortal.mockResolvedValue({
      portal_url: "https://billing.example.com",
    });
  });

  it("test_renders_nothing_when_active", () => {
    const { container } = render(
      <PaymentWarningBanner subscriptionStatus="active" />,
    );

    expect(container.firstChild).toBeNull();
  });

  it("test_renders_amber_banner_when_past_due", () => {
    render(<PaymentWarningBanner subscriptionStatus="past_due" />);

    expect(screen.getByText(/payment failed/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /retry/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /fix payment/i }),
    ).toBeInTheDocument();
  });

  it("test_renders_blue_banner_when_paused", () => {
    render(<PaymentWarningBanner subscriptionStatus="paused" />);

    expect(screen.getByText(/subscription paused/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /reactivate/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /retry/i }),
    ).not.toBeInTheDocument();
  });

  it("test_retry_payment_success_shows_confirmation", async () => {
    mockedRetryPayment.mockResolvedValue({
      retry_initiated: true,
      invoice_id: "in_123",
    });

    render(<PaymentWarningBanner subscriptionStatus="past_due" />);
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));

    expect(
      await screen.findByText("Payment retried — check back shortly."),
    ).toBeInTheDocument();
  });

  it("test_retry_payment_card_error_shows_detail", async () => {
    mockedRetryPayment.mockRejectedValue(new ApiError("Insufficient funds", 402));

    render(<PaymentWarningBanner subscriptionStatus="past_due" />);
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));

    expect(await screen.findByText("Insufficient funds")).toBeInTheDocument();
  });

  it("test_retry_button_disabled_while_in_flight", async () => {
    mockedRetryPayment.mockReturnValue(new Promise(() => undefined));

    render(<PaymentWarningBanner subscriptionStatus="past_due" />);
    const retryButton = screen.getByRole("button", { name: /retry/i });
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(retryButton).toBeDisabled();
    });
  });
});
