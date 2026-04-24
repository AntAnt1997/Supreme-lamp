import { Button } from "@/components/ui/button";
import { Check } from "lucide-react";

const plans = [
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
    <section id="pricing" className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <p className="text-blue-600 font-semibold text-sm uppercase tracking-wider mb-3">
            Pricing
          </p>
          <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
            Simple, Transparent Pricing
          </h2>
          <p className="text-xl text-gray-500 max-w-2xl mx-auto">
            Choose the plan that fits your needs. Upgrade or downgrade at any time.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-stretch">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative rounded-2xl p-8 flex flex-col gap-6 border transition-all duration-300
                ${plan.highlighted
                  ? "border-blue-500 bg-blue-600 text-white shadow-2xl shadow-blue-200 scale-105"
                  : "border-gray-100 bg-white shadow-sm hover:shadow-lg"}`}
            >
              {plan.highlighted && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <span className="bg-gradient-to-r from-yellow-400 to-orange-400 text-white text-xs font-bold px-4 py-1.5 rounded-full">
                    Most Popular
                  </span>
                </div>
              )}

              <div>
                <h3 className={`text-xl font-bold mb-1 ${plan.highlighted ? "text-white" : "text-gray-900"}`}>
                  {plan.name}
                </h3>
                <p className={`text-sm ${plan.highlighted ? "text-blue-100" : "text-gray-500"}`}>
                  {plan.description}
                </p>
              </div>

              <div className="flex items-end gap-1">
                <span className={`text-5xl font-bold ${plan.highlighted ? "text-white" : "text-gray-900"}`}>
                  {plan.price}
                </span>
                <span className={`text-sm mb-2 ${plan.highlighted ? "text-blue-100" : "text-gray-500"}`}>
                  {plan.period}
                </span>
              </div>

              <ul className="space-y-3 flex-1">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-3">
                    <div className={`flex-shrink-0 h-5 w-5 rounded-full flex items-center justify-center
                      ${plan.highlighted ? "bg-white/20" : "bg-blue-50"}`}>
                      <Check className={`h-3 w-3 ${plan.highlighted ? "text-white" : "text-blue-600"}`} />
                    </div>
                    <span className={`text-sm ${plan.highlighted ? "text-blue-50" : "text-gray-600"}`}>
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>

              <Button
                className={`w-full ${plan.highlighted
                  ? "bg-white text-blue-600 hover:bg-blue-50"
                  : ""}`}
                variant={plan.highlighted ? "secondary" : "default"}
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
