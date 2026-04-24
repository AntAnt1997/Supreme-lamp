import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Shield, Clock, Star } from "lucide-react";

export default function Hero() {
  return (
    <section className="relative bg-gray-950 min-h-screen flex items-center overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-900/30 via-gray-950 to-purple-900/20 pointer-events-none" />
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-32 text-center">
        <Badge variant="outline" className="mb-6 text-blue-400 border-blue-500/40 bg-blue-500/10">
          🚀 Now in Beta — Join 10,000+ users
        </Badge>

        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-white leading-tight tracking-tight mb-6">
          AI Medical Workers
          <br />
          <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Available 24/7
          </span>
        </h1>

        <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          Your personal AI health team — always on, always ready. Get instant symptom analysis, medication reminders, appointment scheduling, and continuous health monitoring around the clock.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
          <Button size="lg" className="gap-2 bg-blue-600 hover:bg-blue-500">
            Get Started Free <ArrowRight className="h-5 w-5" />
          </Button>
          <Button size="lg" variant="outline">
            Watch Demo
          </Button>
        </div>

        {/* Trust badges */}
        <div className="flex flex-wrap justify-center gap-6 text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-green-400" />
            <span>HIPAA Compliant</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-blue-400" />
            <span>24/7 Availability</span>
          </div>
          <div className="flex items-center gap-2">
            <Star className="h-4 w-4 text-yellow-400" />
            <span>4.9/5 Rating</span>
          </div>
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-purple-400" />
            <span>256-bit Encryption</span>
          </div>
        </div>
      </div>
    </section>
  );
}
