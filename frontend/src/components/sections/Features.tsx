import {
  Brain,
  Calendar,
  Bell,
  FileText,
  MessageSquare,
  Activity,
  type LucideIcon,
} from "lucide-react";

interface Feature {
  icon: LucideIcon;
  title: string;
  description: string;
  color: string;
  bg: string;
}

const features: Feature[] = [
  {
    icon: Brain,
    title: "AI Symptom Analysis",
    description:
      "Advanced AI analyzes your symptoms and provides instant preliminary assessments based on medical knowledge.",
    color: "text-blue-400",
    bg: "bg-blue-500/10",
  },
  {
    icon: Calendar,
    title: "Smart Scheduling",
    description:
      "Automatically schedule appointments with the right specialists based on your medical needs.",
    color: "text-purple-400",
    bg: "bg-purple-500/10",
  },
  {
    icon: Bell,
    title: "Medication Reminders",
    description:
      "Never miss a dose with intelligent medication tracking and personalized reminder systems.",
    color: "text-green-400",
    bg: "bg-green-500/10",
  },
  {
    icon: FileText,
    title: "Medical Records",
    description:
      "Securely store, organize and share your medical records with healthcare providers instantly.",
    color: "text-orange-400",
    bg: "bg-orange-500/10",
  },
  {
    icon: MessageSquare,
    title: "24/7 Health Chat",
    description:
      "Chat with our AI medical workers any time of day or night for immediate health guidance.",
    color: "text-pink-400",
    bg: "bg-pink-500/10",
  },
  {
    icon: Activity,
    title: "Health Monitoring",
    description:
      "Continuous monitoring of your health metrics with proactive alerts and recommendations.",
    color: "text-cyan-400",
    bg: "bg-cyan-500/10",
  },
];

export default function Features() {
  return (
    <section id="services" className="bg-gray-900 py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Everything You Need for Better Health
          </h2>
          <p className="text-gray-400 max-w-xl mx-auto text-lg">
            Our AI medical workers handle the routine so your human doctors can focus on what matters most.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f) => (
            <div
              key={f.title}
              className="bg-gray-800/50 border border-white/5 rounded-2xl p-6 hover:border-blue-500/30 transition-colors group"
            >
              <div className={`${f.bg} inline-flex rounded-xl p-3 mb-4`}>
                <f.icon className={`h-6 w-6 ${f.color}`} />
              </div>
              <h3 className="text-white font-semibold text-lg mb-2">{f.title}</h3>
              <p className="text-gray-400 text-sm leading-relaxed">{f.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
