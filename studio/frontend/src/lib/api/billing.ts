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
