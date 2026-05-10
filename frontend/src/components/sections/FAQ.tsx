import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

interface FAQ {
  question: string;
  answer: string;
}

const faqs: FAQ[] = [
  {
    question: "Is this safe to run fully unattended on day one?",
    answer:
      "No. The recommended rollout is to begin with manual approval enabled, small trade sizes, and close monitoring until the system proves stable in your environment.",
  },
  {
    question: "What infrastructure does the stack expect?",
    answer:
      "The architecture is built around PostgreSQL, a cloud worker host such as Railway or Render, EVM RPC access, and notification providers like Telegram, Discord, email, and optional SMS.",
  },
  {
    question: "Which safety rails are included before a trade is sent?",
    answer:
      "The system applies per-trade limits, daily loss caps, concentration checks, gas ceilings, slippage protection, kill switches, and optional manual approvals before execution.",
  },
  {
    question: "What does the notification system cover?",
    answer:
      "It supports priority-based routing to Telegram, Discord, email, SMS, plus daily summaries so operators can respond differently to informational events versus critical incidents.",
  },
  {
    question: "How should I start funding and sizing trades?",
    answer:
      "Start with a small balance, test $10-$50 trades, monitor the first week closely, and only increase limits once the execution path, alerts, and safety controls have been verified.",
  },
];

export default function FAQ() {
  return (
    <section id="faq" className="bg-gray-950 py-24">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Frequently Asked Questions
          </h2>
          <p className="text-gray-400 max-w-xl mx-auto text-lg">
            Have questions? We've got answers.
          </p>
        </div>

        <Accordion type="single" collapsible className="text-white">
          {faqs.map((faq, i) => (
            <AccordionItem key={i} value={`item-${i}`}>
              <AccordionTrigger className="text-left text-base">
                {faq.question}
              </AccordionTrigger>
              <AccordionContent className="text-base">
                {faq.answer}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  );
}
