import {
  Bot,
  Database,
  Bell,
  ArrowLeftRight,
  ShieldCheck,
  Workflow,
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
    icon: Bot,
    title: "Autonomous Worker Mesh",
    description:
      "Run signal monitoring, price analysis, risk reviews, execution, research, and arbitrage scans on staggered schedules around the clock.",
    color: "text-blue-400",
    bg: "bg-blue-500/10",
  },
  {
    icon: Database,
    title: "PostgreSQL Trading Ledger",
    description:
      "Persist wallets, signals, trades, open positions, daily metrics, and AI insights in one schema ready for Supabase or RDS.",
    color: "text-purple-400",
    bg: "bg-purple-500/10",
  },
  {
    icon: Bell,
    title: "Priority Notifications",
    description:
      "Route low, medium, high, and critical events to Telegram, Discord, email, SMS, and daily operator summaries.",
    color: "text-green-400",
    bg: "bg-green-500/10",
  },
  {
    icon: ArrowLeftRight,
    title: "Uniswap V3 Execution",
    description:
      "Simulate trades, find the best fee tier, manage approvals, optimize gas, and enforce slippage limits before every order.",
    color: "text-orange-400",
    bg: "bg-orange-500/10",
  },
  {
    icon: ShieldCheck,
    title: "Capital Protection Rails",
    description:
      "Enforce daily loss caps, per-trade limits, concentration guards, gas ceilings, kill switches, and manual review workflows.",
    color: "text-pink-400",
    bg: "bg-pink-500/10",
  },
  {
    icon: Workflow,
    title: "Operator API Server",
    description:
      "Control workers, inspect trades and positions, manage safety settings, and expose analytics through a RESTful backend.",
    color: "text-cyan-400",
    bg: "bg-cyan-500/10",
  },
];

export default function Features() {
  return (
    <section id="components" className="bg-gray-900 py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            The Five Core Components, Plus Operations
          </h2>
          <p className="text-gray-400 max-w-xl mx-auto text-lg">
            Everything needed to run a monitored AI trading operation from signal discovery through execution, risk, and reporting.
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
