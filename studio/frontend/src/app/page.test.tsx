import { render, screen } from "@testing-library/react";

jest.mock("remark-gfm", () => ({
  __esModule: true,
  default: () => undefined,
}));

jest.mock("react-markdown", () => {
  const MockReactMarkdown = ({ children }: { children: string }): JSX.Element => {
    const lines = children.split("\n");
    return (
      <div>
        {lines.map((line, index) => {
          if (line.startsWith("## ")) {
            return <h2 key={`h2-${index}`}>{line.replace("## ", "")}</h2>;
          }
          return <p key={`p-${index}`}>{line}</p>;
        })}
      </div>
    );
  };
  return {
    __esModule: true,
    default: MockReactMarkdown,
  };
});

import CtaSection from "@/components/landing/CtaSection";
import ExampleReportSection from "@/components/landing/ExampleReportSection";
import FaqSection from "@/components/landing/FaqSection";
import FeaturesSection from "@/components/landing/FeaturesSection";
import Footer from "@/components/landing/Footer";
import HeroSection from "@/components/landing/HeroSection";
import HowItWorksSection from "@/components/landing/HowItWorksSection";
import NavBar from "@/components/landing/NavBar";
import SocialProofBar from "@/components/landing/SocialProofBar";

describe("Landing page sections", () => {
  it("test_landing_page_renders_hero_heading", () => {
    render(<HeroSection />);
    expect(
      screen.getByRole("heading", { level: 1, name: /market research reports/i }),
    ).toBeInTheDocument();
  });

  it("test_landing_page_renders_cta_buttons", () => {
    render(<HeroSection />);
    expect(
      screen.getByRole("link", { name: /generate your first report/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /see a sample report/i })).toBeInTheDocument();
  });

  it("test_social_proof_bar_renders_four_stats", () => {
    render(<SocialProofBar />);
    expect(screen.getByText(/reports generated/i)).toBeInTheDocument();
    expect(screen.getByText(/sources per report/i)).toBeInTheDocument();
    expect(screen.getByText(/avg\. generation/i)).toBeInTheDocument();
    expect(screen.getByText(/ai agents per report/i)).toBeInTheDocument();
  });

  it("test_how_it_works_renders_four_steps", () => {
    render(<HowItWorksSection />);
    expect(screen.getByText("Researcher")).toBeInTheDocument();
    expect(screen.getByText("Planner")).toBeInTheDocument();
    expect(screen.getByText("Writer")).toBeInTheDocument();
    expect(screen.getByText("QA Specialist")).toBeInTheDocument();
  });

  it("test_features_section_renders_six_cards", () => {
    render(<FeaturesSection />);
    expect(screen.getByText("Live web research")).toBeInTheDocument();
    expect(screen.getByText("Vector knowledge base")).toBeInTheDocument();
    expect(screen.getByText("PDF + Markdown export")).toBeInTheDocument();
    expect(screen.getByText("Under 90 seconds")).toBeInTheDocument();
    expect(screen.getByText("Fact-checked output")).toBeInTheDocument();
    expect(screen.getByText("Your data stays yours")).toBeInTheDocument();
  });

  it("test_example_report_renders_content", () => {
    render(<ExampleReportSection />);
    expect(screen.getByRole("heading", { name: /executive summary/i })).toBeInTheDocument();
    expect(screen.getByText(/\$67\.4 billion/i)).toBeInTheDocument();
  });

  it("test_faq_renders_eight_questions", () => {
    render(<FaqSection />);
    expect(screen.getByText("How is this different from just asking ChatGPT?")).toBeInTheDocument();
    expect(screen.getByText("What topics work best?")).toBeInTheDocument();
    expect(screen.getByText("How current is the research?")).toBeInTheDocument();
    expect(screen.getByText("Can I edit the report after it's generated?")).toBeInTheDocument();
    expect(screen.getByText("Is my data private?")).toBeInTheDocument();
    expect(screen.getByText("What if the report quality is poor?")).toBeInTheDocument();
    expect(screen.getByText("Can I use Studio for client deliverables?")).toBeInTheDocument();
    expect(screen.getByText("Do you offer a free trial?")).toBeInTheDocument();
  });

  it("test_cta_section_button_links_to_signup", () => {
    render(<CtaSection />);
    const ctaLink = screen.getByRole("link", { name: /generate your first report/i });
    expect(ctaLink).toHaveAttribute("href", expect.stringContaining("/auth/signup"));
  });

  it("test_navbar_get_started_links_to_signup", () => {
    render(<NavBar />);
    const signupLink = screen.getByRole("link", { name: /get started/i });
    expect(signupLink).toHaveAttribute("href", "/auth/signup");
  });

  it("test_footer_renders_legal_links", () => {
    render(<Footer />);
    expect(screen.getByRole("link", { name: /privacy policy/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /terms of service/i })).toBeInTheDocument();
  });
});
