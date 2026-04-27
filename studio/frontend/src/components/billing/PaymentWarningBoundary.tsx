"use client";

import { useEffect, useState } from "react";

import { PaymentWarningBanner } from "@/components/billing/PaymentWarningBanner";
import { useSupabaseAccessToken } from "@/hooks/useSupabaseAccessToken";
import { getPaymentStatus } from "@/lib/api/billing";

export const PaymentWarningBoundary = (): JSX.Element | null => {
  const { token } = useSupabaseAccessToken();
  const [subscriptionStatus, setSubscriptionStatus] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setSubscriptionStatus(null);
      return;
    }

    let isMounted = true;

    const loadStatus = async (): Promise<void> => {
      try {
        const status = await getPaymentStatus(token);
        if (isMounted) {
          setSubscriptionStatus(status.subscription_status);
        }
      } catch {
        if (isMounted) {
          setSubscriptionStatus(null);
        }
      }
    };

    void loadStatus();

    return () => {
      isMounted = false;
    };
  }, [token]);

  return <PaymentWarningBanner subscriptionStatus={subscriptionStatus} />;
};
