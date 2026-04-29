"use client";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const faqs = [
  {
    question: "How is this different from just asking ChatGPT?",
    answer:
      "ChatGPT is a single model answering from training data. Studio uses four specialised agents that search the live web, index real sources, write from a structured plan, and fact-check the output - producing a document, not a chat reply.",
  },
  {
    question: "What topics work best?",
    answer:
      "Market analysis, competitor overviews, industry trend reports, and technology landscape summaries. Studio works best for structured business research with a clear scope.",
  },
  {
    question: "How current is the research?",
    answer:
      "Agents search the live web at generation time - results reflect what is available online today, not a training cutoff.",
  },
  {
    question: "Can I edit the report after it's generated?",
    answer:
      "Yes. Download as Markdown and edit in any text editor, Notion, or Google Docs. The PDF is the final formatted version.",
  },
  {
    question: "Is my data private?",
    answer:
      "Yes. Reports are private to your account. We do not use your reports or topics to train any models.",
  },
  {
    question: "What if the report quality is poor?",
    answer:
      "We refund your credit automatically if generation fails. If the quality is not what you expected, contact support and we will make it right.",
  },
  {
    question: "Can I use Studio for client deliverables?",
    answer:
      "Yes. Agency plan users get white-label PDF headers. The output is yours to use however you like.",
  },
  {
    question: "Do you offer a free trial?",
    answer:
      "The Free plan gives you 2 reports per month forever - no credit card required. It is a permanent free tier, not a trial.",
  },
];

export default function FaqSection(): JSX.Element {
  return (
    <section className="px-4 py-16 sm:px-6" aria-labelledby="faq-heading">
      <div className="mx-auto w-full max-w-2xl">
        <div className="text-center">
          <h2 id="faq-heading" className="text-3xl font-semibold text-neutral-900">
            Frequently asked questions
          </h2>
        </div>

        <Accordion type="single" collapsible className="mt-8 w-full">
          {faqs.map((faq, index) => (
            <AccordionItem key={faq.question} value={`item-${index + 1}`}>
              <AccordionTrigger>{faq.question}</AccordionTrigger>
              <AccordionContent>{faq.answer}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  );
}
