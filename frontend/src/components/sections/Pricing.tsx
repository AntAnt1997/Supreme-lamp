import { Button } from "@/components/ui/button";
import { Check } from "lucide-react";

interface Plan {
  name: string;
  price: string;
  period: string;
  description: string;
  features: string[];
  cta: string;
  highlighted: boolean;
}

const plans: Plan[] = [
  {
    name: "Basic",
    price: "$9",
    period: "/month",
    description: "Perfect for individuals managing their health",
    features: [
      "AI symptom checker",
      "Medication reminders",
      "Basic health monitoring",
      "Email support",
      "1 user profile",
    ],
    cta: "Get Started",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "$29",
    period: "/month",
    description: "Ideal for families and chronic condition management",
    features: [
      "Everything in Basic",
      "24/7 AI health chat",
      "Smart appointment scheduling",
      "Medical records storage",
      "Up to 5 user profiles",
      "Priority support",
    ],
    cta: "Start Free Trial",
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: "$99",
    period: "/month",
    description: "For healthcare providers and organizations",
    features: [
      "Everything in Pro",
      "Unlimited user profiles",
      "Custom AI workflows",
      "EHR integration",
      "Dedicated account manager",
      "HIPAA compliance tools",
    ],
    cta: "Contact Sales",
    highlighted: false,
  },
];

export default function Pricing() {
  return (
    <section id="pricing" className="bg-gray-900 py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Simple, Transparent Pricing
          </h2>
          <p className="text-gray-400 max-w-xl mx-auto text-lg">
            No hidden fees. Cancel anytime. Start free with our 14-day trial.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`rounded-2xl p-8 flex flex-col gap-6 border transition-all ${
                plan.highlighted
                  ? "bg-blue-600 border-blue-400 scale-105 shadow-2xl shadow-blue-500/20"
                  : "bg-gray-800/50 border-white/5"
              }`}
            >
              <div>
                <h3
                  className={`font-bold text-lg mb-1 ${
                    plan.highlighted ? "text-white" : "text-white"
                  }`}
                >
                  {plan.name}
                </h3>
                <p
                  className={`text-sm ${
                    plan.highlighted ? "text-blue-100" : "text-gray-400"
                  }`}
                >
                  {plan.description}
                </p>
              </div>

              <div className="flex items-end gap-1">
                <span className="text-4xl font-bold text-white">{plan.price}</span>
                <span
                  className={`text-sm mb-1 ${
                    plan.highlighted ? "text-blue-200" : "text-gray-400"
                  }`}
                >
                  {plan.period}
                </span>
              </div>

              <ul className="space-y-3 flex-1">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-2 text-sm">
                    <Check
                      className={`h-4 w-4 shrink-0 ${
                        plan.highlighted ? "text-white" : "text-blue-400"
                      }`}
                    />
                    <span
                      className={plan.highlighted ? "text-blue-50" : "text-gray-300"}
                    >
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>

              <Button
                variant={plan.highlighted ? "outline" : "default"}
                className={
                  plan.highlighted
                    ? "border-white text-white hover:bg-white hover:text-blue-600 w-full"
                    : "w-full"
                }
              >
                {plan.cta}
              </Button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
