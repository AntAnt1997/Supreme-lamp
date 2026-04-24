import {
  Brain,
  Calendar,
  Bell,
  FileText,
  MessageSquare,
  Activity,
} from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "AI Symptom Analysis",
    description:
      "Advanced AI analyzes your symptoms and provides instant preliminary assessments based on medical knowledge.",
    color: "text-blue-500",
    bg: "bg-blue-500/10",
  },
  {
    icon: Calendar,
    title: "Smart Scheduling",
    description:
      "Automatically schedule appointments with the right specialists based on your medical needs.",
    color: "text-purple-500",
    bg: "bg-purple-500/10",
  },
  {
    icon: Bell,
    title: "Medication Reminders",
    description:
      "Never miss a dose with intelligent medication tracking and personalized reminder systems.",
    color: "text-green-500",
    bg: "bg-green-500/10",
  },
  {
    icon: FileText,
    title: "Medical Records",
    description:
      "Securely store, organize and share your medical records with healthcare providers instantly.",
    color: "text-orange-500",
    bg: "bg-orange-500/10",
  },
  {
    icon: MessageSquare,
    title: "24/7 Health Chat",
    description:
      "Chat with our AI medical workers any time of day or night for immediate health guidance.",
    color: "text-pink-500",
    bg: "bg-pink-500/10",
  },
  {
    icon: Activity,
    title: "Health Monitoring",
    description:
      "Continuous monitoring of your health metrics with proactive alerts and recommendations.",
    color: "text-cyan-500",
    bg: "bg-cyan-500/10",
  },
];

export default function Features() {
  return (
    <section id="services" className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <p className="text-blue-600 font-semibold text-sm uppercase tracking-wider mb-3">
            What We Offer
          </p>
          <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
            Everything You Need,{" "}
            <span className="text-blue-600">All in One Place</span>
          </h2>
          <p className="text-xl text-gray-500 max-w-2xl mx-auto">
            Our AI medical workers handle every aspect of your healthcare management so you can focus on living well.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.title}
                className="group rounded-2xl border border-gray-100 bg-white p-6 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
              >
                <div className={`inline-flex h-12 w-12 items-center justify-center rounded-xl ${feature.bg} mb-4`}>
                  <Icon className={`h-6 w-6 ${feature.color}`} />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{feature.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
