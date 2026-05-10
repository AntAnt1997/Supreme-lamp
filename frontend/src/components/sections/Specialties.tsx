interface Specialty {
  name: string;
  icon: string;
  count: string;
}

const specialties: Specialty[] = [
  { name: "Ethereum", icon: "⟠", count: "Uniswap mainnet" },
  { name: "Polygon", icon: "🟣", count: "Low-cost routing" },
  { name: "Arbitrum", icon: "🔵", count: "Fast execution" },
  { name: "Optimism", icon: "🔴", count: "Rollup support" },
  { name: "Telegram", icon: "✈️", count: "Real-time actions" },
  { name: "Discord", icon: "💬", count: "Rich embeds" },
  { name: "Email + SMS", icon: "📨", count: "Critical paging" },
  { name: "PostgreSQL", icon: "🗄️", count: "Signals + PnL" },
];

export default function Specialties() {
  return (
    <section id="integrations" className="bg-gray-900 py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Integrations and Runtime Targets
          </h2>
          <p className="text-gray-400 max-w-xl mx-auto text-lg">
            Deploy on the chains, notification channels, and data services that keep a trading desk responsive.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {specialties.map((s) => (
            <div
              key={s.name}
              className="bg-gray-800/50 border border-white/5 rounded-2xl p-5 text-center hover:border-blue-500/30 hover:bg-gray-800 transition-all group cursor-default"
            >
              <div className="text-4xl mb-3">{s.icon}</div>
              <h3 className="text-white font-medium text-sm mb-1">{s.name}</h3>
              <p className="text-gray-500 text-xs">{s.count}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
