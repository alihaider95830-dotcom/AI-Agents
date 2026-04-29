export interface PricingPlan {
  name: string;
  price: string;
  summary: string;
  features: string[];
}

export const pricingPlans: PricingPlan[] = [
  {
    name: "Free",
    price: "$0",
    summary: "For trying the report pipeline.",
    features: ["2 reports per month", "Markdown exports", "Core dashboard"],
  },
  {
    name: "Pro",
    price: "$29",
    summary: "For solo operators and research-heavy workflows.",
    features: ["20 reports per month", "PDF exports", "Priority generation"],
  },
  {
    name: "Agency",
    price: "$99",
    summary: "For teams running recurring client research.",
    features: ["High-volume report credits", "Billing portal", "Admin controls"],
  },
];
