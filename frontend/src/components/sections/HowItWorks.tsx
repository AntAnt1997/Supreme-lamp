const steps = [
  {
    step: "01",
    title: "Connect Data, Keys, and Alerts",
    description:
      "Configure your database, RPC provider, AI credentials, messaging channels, and initial trade limits before any automation starts.",
  },
  {
    step: "02",
    title: "Run the Worker Loop",
    description:
      "Workers watch tracked wallets, research markets, score setups, and queue trades while the API layer exposes controls and telemetry.",
  },
  {
    step: "03",
    title: "Approve, Execute, and Monitor",
    description:
      "Safety rails validate every action, real-time notifications surface key events, and PnL plus risk metrics stay visible at all times.",
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="bg-gray-950 py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">How It Works</h2>
          <p className="text-gray-400 max-w-xl mx-auto text-lg">
            Start in manual approval mode, validate each layer, then scale into a continuously running production workflow.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
          {/* Connector line (desktop) */}
          <div className="hidden md:block absolute top-10 left-1/3 right-1/3 h-px bg-gradient-to-r from-blue-500/50 to-purple-500/50" />

          {steps.map((s, i) => (
            <div key={s.step} className="text-center relative">
              <div
                className="mx-auto mb-6 w-20 h-20 rounded-full flex items-center justify-center text-2xl font-bold border-2 border-blue-500/50 bg-blue-500/10 text-blue-400"
                style={{ background: `linear-gradient(135deg, rgba(59,130,246,${0.1 + i * 0.05}), rgba(139,92,246,${0.05 + i * 0.05}))` }}
              >
                {s.step}
              </div>
              <h3 className="text-white font-semibold text-xl mb-3">{s.title}</h3>
              <p className="text-gray-400 leading-relaxed">{s.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
