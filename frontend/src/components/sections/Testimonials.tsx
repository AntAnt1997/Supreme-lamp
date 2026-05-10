import { Star } from "lucide-react";

interface Testimonial {
  name: string;
  role: string;
  avatar: string;
  rating: number;
  text: string;
}

const testimonials: Testimonial[] = [
  {
    name: "Marcus Lee",
    role: "Quant Operator",
    avatar: "ML",
    rating: 5,
    text: "The worker split makes it easy to keep signal discovery, execution, and monitoring isolated while still seeing every trade in one place.",
  },
  {
    name: "Priya Shah",
    role: "DevOps Lead",
    avatar: "PS",
    rating: 5,
    text: "Manual approvals, alerts, and daily summaries gave our team enough confidence to start small and expand automation safely.",
  },
  {
    name: "Jonah Brooks",
    role: "Research Trader",
    avatar: "JB",
    rating: 5,
    text: "I like that the deployment story is practical: database, cloud worker, notifications, and guardrails instead of hype with no controls.",
  },
];

export default function Testimonials() {
  return (
    <section className="bg-gray-950 py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Built for Hands-On Operators
          </h2>
          <p className="text-gray-400 max-w-xl mx-auto text-lg">
            Teams use the stack to launch cautiously, monitor closely, and keep human oversight in the loop.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {testimonials.map((t) => (
            <div
              key={t.name}
              className="bg-gray-800/50 border border-white/5 rounded-2xl p-6 flex flex-col gap-4"
            >
              {/* Stars */}
              <div className="flex gap-1">
                {Array.from({ length: t.rating }).map((_, i) => (
                  <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                ))}
              </div>

              <p className="text-gray-300 text-sm leading-relaxed flex-1">"{t.text}"</p>

              {/* Author */}
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold shrink-0">
                  {t.avatar}
                </div>
                <div>
                  <p className="text-white font-medium text-sm">{t.name}</p>
                  <p className="text-gray-500 text-xs">{t.role}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
