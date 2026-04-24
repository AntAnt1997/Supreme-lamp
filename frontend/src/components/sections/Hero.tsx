import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Shield, Clock, Star } from "lucide-react";

export default function Hero() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-indigo-50 py-24 sm:py-32">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-blue-100/60 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-indigo-100/60 blur-3xl" />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <Badge variant="secondary" className="mb-6 gap-1.5 px-4 py-1.5 text-blue-700 bg-blue-50 border-blue-200">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
          </span>
          AI Medical Workers Online 24/7
        </Badge>

        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-gray-900 tracking-tight mb-6">
          Healthcare That Never{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">
            Sleeps
          </span>
        </h1>

        <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-10 leading-relaxed">
          Meet your AI medical team — intelligent workers available around the clock to monitor your health, answer questions, schedule appointments, and give you peace of mind every hour of the day.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
          <Button size="lg" className="gap-2 text-base px-8 h-12">
            Start for Free <ArrowRight className="h-5 w-5" />
          </Button>
          <Button size="lg" variant="outline" className="text-base px-8 h-12">
            Watch Demo
          </Button>
        </div>

        {/* Trust badges */}
        <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-green-500" />
            <span>HIPAA Compliant</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-blue-500" />
            <span>24/7 Availability</span>
          </div>
          <div className="flex items-center gap-2">
            <Star className="h-5 w-5 text-yellow-500" />
            <span>4.9 / 5 Rating</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-blue-500 font-semibold">50K+</span>
            <span>Patients Served</span>
          </div>
        </div>

        {/* Hero visual */}
        <div className="mt-20 relative max-w-4xl mx-auto">
          <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 p-6 text-left">
            <div className="flex items-center gap-3 mb-4">
              <div className="h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm">AI</div>
              <div>
                <p className="font-semibold text-gray-900 text-sm">MediAI Assistant</p>
                <p className="text-xs text-green-500 flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-green-500 inline-block" /> Online
                </p>
              </div>
            </div>
            <div className="space-y-3">
              <div className="bg-gray-50 rounded-xl rounded-tl-none p-3 text-sm text-gray-700 max-w-md">
                Good morning! I've reviewed your health metrics. Your blood pressure is trending well. Shall I reschedule your cardiologist follow-up for next week?
              </div>
              <div className="bg-blue-600 rounded-xl rounded-tr-none p-3 text-sm text-white max-w-md ml-auto text-right">
                Yes, please book Thursday afternoon if available.
              </div>
              <div className="bg-gray-50 rounded-xl rounded-tl-none p-3 text-sm text-gray-700 max-w-md">
                Done! ✅ Appointment confirmed for Thursday at 2:30 PM with Dr. Chen. I've also sent you a reminder and updated your health records.
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
