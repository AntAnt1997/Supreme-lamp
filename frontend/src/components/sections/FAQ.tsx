import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const faqs = [
  {
    question: "Is MediAI a replacement for my doctor?",
    answer:
      "No. MediAI is designed to complement your existing healthcare, not replace it. Our AI workers provide guidance, monitoring, and support but always recommend consulting a licensed physician for diagnosis and treatment.",
  },
  {
    question: "How is my medical data protected?",
    answer:
      "We take data security extremely seriously. All data is encrypted at rest and in transit, we are fully HIPAA compliant, and we never sell your personal health information to third parties.",
  },
  {
    question: "What happens in a medical emergency?",
    answer:
      "In any emergency situation, our AI workers will immediately direct you to call 911 or your local emergency services. MediAI is not designed for emergency medical situations.",
  },
  {
    question: "Can I use MediAI for my children?",
    answer:
      "Yes, our Pro and Enterprise plans support multiple user profiles including children. Parents or guardians manage child profiles and all pediatric guidance is age-appropriate.",
  },
  {
    question: "How accurate is the AI symptom checker?",
    answer:
      "Our AI is trained on millions of medical cases and peer-reviewed literature. However, it provides informational guidance only and accuracy varies. Always consult a healthcare professional for diagnosis.",
  },
];

export default function FAQ() {
  return (
    <section id="faq" className="py-24 bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <p className="text-blue-600 font-semibold text-sm uppercase tracking-wider mb-3">
            FAQ
          </p>
          <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
            Frequently Asked Questions
          </h2>
          <p className="text-xl text-gray-500">
            Have questions? We've got answers.
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 px-8 py-2">
          <Accordion type="single" collapsible className="w-full">
            {faqs.map((faq, index) => (
              <AccordionItem key={index} value={`item-${index}`}>
                <AccordionTrigger className="text-left text-gray-900 font-medium hover:no-underline hover:text-blue-600">
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent>
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </div>
    </section>
  );
}
