import { render, screen } from "@testing-library/react";

import PrivacyPolicyPage from "@/app/legal/privacy/page";

describe("Privacy policy page", () => {
  it("test_privacy_page_renders_heading", () => {
    render(<PrivacyPolicyPage />);
    expect(screen.getByRole("heading", { level: 1, name: /privacy policy/i })).toBeInTheDocument();
  });

  it("test_privacy_page_has_contact_email", () => {
    render(<PrivacyPolicyPage />);
    expect(screen.getByText(/privacy@yourdomain\.com/i)).toBeInTheDocument();
  });
});
