import { Star } from "lucide-react";

const testimonials = [
  {
    name: "Sarah Johnson",
    role: "Patient",
    avatar: "SJ",
    rating: 5,
    text: "MediAI has completely transformed how I manage my chronic condition. Having 24/7 access to medical guidance gives me incredible peace of mind.",
  },
  {
    name: "Dr. Michael Chen",
    role: "Healthcare Provider",
    avatar: "MC",
    rating: 5,
    text: "As a physician, I recommend MediAI to my patients for between-visit support. The AI workers are accurate and always know when to escalate to human care.",
  },
  {
    name: "Emily Rodriguez",
    role: "Caregiver",
    avatar: "ER",
    rating: 5,
    text: "Managing my elderly mother's medications and appointments used to be overwhelming. MediAI handles everything seamlessly.",
  },
];

export default function Testimonials() {
  return (
    <section className="py-24 bg-gradient-to-br from-blue-50 to-indigo-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <p className="text-blue-600 font-semibold text-sm uppercase tracking-wider mb-3">
            Testimonials
          </p>
          <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
            Trusted by Patients &amp; Providers
          </h2>
          <p className="text-xl text-gray-500 max-w-2xl mx-auto">
            See what real users say about their experience with MediAI.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {testimonials.map((t) => (
            <div
              key={t.name}
              className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 flex flex-col gap-4"
            >
              {/* Stars */}
              <div className="flex gap-1">
                {Array.from({ length: t.rating }).map((_, i) => (
                  <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                ))}
              </div>
              {/* Quote */}
              <p className="text-gray-600 leading-relaxed flex-1">"{t.text}"</p>
              {/* Author */}
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold text-sm">
                  {t.avatar}
                </div>
                <div>
                  <p className="font-semibold text-gray-900 text-sm">{t.name}</p>
                  <p className="text-xs text-gray-400">{t.role}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
