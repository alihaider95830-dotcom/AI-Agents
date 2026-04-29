import { apiRequest } from "@/lib/api/client";

export interface UsageSummary {
  tier: "free" | "pro" | "agency";
  credits_remaining: number;
  reports_this_month: number;
  monthly_limit: number | null;
  resets_on: string;
}

export const getUsageSummary = async (
  token: string,
): Promise<UsageSummary> => apiRequest<UsageSummary>("/billing/usage", token);

export interface PaymentStatus {
  subscription_status: string | null;
  is_past_due: boolean;
  is_paused: boolean;
  tier: string;
  action_required: boolean;
}

export interface RetryPaymentResponse {
  retry_initiated: boolean;
  invoice_id: string;
}

export interface PortalResponse {
  portal_url: string;
}

export const getPaymentStatus = async (
  token: string,
): Promise<PaymentStatus> =>
  apiRequest<PaymentStatus>("/billing/payment-status", token);

export const retryPayment = async (
  token: string,
): Promise<RetryPaymentResponse> =>
  apiRequest<RetryPaymentResponse>("/billing/retry-payment", token, {
    method: "POST",
  });

export const createBillingPortal = async (
  token: string,
): Promise<PortalResponse> =>
  apiRequest<PortalResponse>("/billing/portal", token, {
    method: "POST",
  });

// ---------------------------------------------------------------------------
// Checkout session
// ---------------------------------------------------------------------------

export interface CheckoutRequest {
  price_id: string;
  success_url: string;
  cancel_url: string;
}

export interface CheckoutResponse {
  checkout_url: string;
}

export const createCheckoutSession = async (
  token: string,
  priceId: string,
  successUrl: string,
  cancelUrl: string,
): Promise<CheckoutResponse> =>
  apiRequest<CheckoutResponse>("/billing/checkout", token, {
    method: "POST",
    body: JSON.stringify({
      price_id: priceId,
      success_url: successUrl,
      cancel_url: cancelUrl,
    }),
  });

// ---------------------------------------------------------------------------
// Subscription detail
// ---------------------------------------------------------------------------

export interface SubscriptionDetail {
  status: string;
  current_period_end?: number | null;
  cancel_at_period_end?: boolean | null;
}

export const getSubscription = async (
  token: string,
): Promise<SubscriptionDetail> =>
  apiRequest<SubscriptionDetail>("/billing/subscription", token);

