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
    <section className="bg-gray-950 py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Trusted by Thousands
          </h2>
          <p className="text-gray-400 max-w-xl mx-auto text-lg">
            See why patients, caregivers, and healthcare providers love MediAI.
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
