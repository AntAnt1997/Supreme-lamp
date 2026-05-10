import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Shield, Clock, Zap } from "lucide-react";

export default function Hero() {
  return (
    <section className="relative bg-gray-950 min-h-screen flex items-center overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-900/30 via-gray-950 to-purple-900/20 pointer-events-none" />
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-32 text-center">
        <Badge variant="outline" className="mb-6 text-blue-400 border-blue-500/40 bg-blue-500/10">
          ⚡ Production architecture for autonomous trading teams
        </Badge>

        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-white leading-tight tracking-tight mb-6">
          24/7 AI Trading
          <br />
          <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            With Safety Rails
          </span>
        </h1>

        <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          Monitor whale wallets, score opportunities with AI, execute Uniswap trades, and keep operators informed through one production-ready control plane.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
          <a href="#components">
            <Button size="lg" className="gap-2 bg-blue-600 hover:bg-blue-500">
              Review Components <ArrowRight className="h-5 w-5" />
            </Button>
          </a>
          <a href="#deployment">
            <Button size="lg" variant="outline">
              Open Deployment Guide
            </Button>
          </a>
        </div>

        {/* Trust badges */}
        <div className="flex flex-wrap justify-center gap-6 text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-green-400" />
            <span>Kill switch + manual approval</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-blue-400" />
            <span>6 autonomous workers</span>
          </div>
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-yellow-400" />
            <span>15s execution loop</span>
          </div>
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-purple-400" />
            <span>4 EVM chains supported</span>
          </div>
        </div>
      </div>
    </section>
  );
}
