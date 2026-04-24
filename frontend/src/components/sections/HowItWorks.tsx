const steps = [
  {
    step: "01",
    title: "Create Your Profile",
    description:
      "Sign up and complete your medical profile including health history, current medications, and preferences.",
  },
  {
    step: "02",
    title: "Connect with AI Workers",
    description:
      "Our AI medical workers are instantly assigned to your case, available around the clock for your needs.",
  },
  {
    step: "03",
    title: "Get Continuous Care",
    description:
      "Receive ongoing support, monitoring, and guidance from your dedicated AI medical team 24/7.",
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <p className="text-blue-600 font-semibold text-sm uppercase tracking-wider mb-3">
            Simple Process
          </p>
          <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
            Up and Running in Minutes
          </h2>
          <p className="text-xl text-gray-500 max-w-2xl mx-auto">
            Getting started with your AI medical team is quick and straightforward.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
          {/* Connector line (desktop) */}
          <div className="hidden md:block absolute top-10 left-1/3 right-1/3 h-0.5 bg-blue-100" />

          {steps.map((step, index) => (
            <div key={step.step} className="relative flex flex-col items-center text-center">
              {/* Step number */}
              <div className={`relative z-10 flex h-20 w-20 items-center justify-center rounded-full border-4 mb-6 font-bold text-2xl
                ${index === 1
                  ? "border-blue-600 bg-blue-600 text-white shadow-lg shadow-blue-200"
                  : "border-blue-100 bg-white text-blue-600"}`}>
                {step.step}
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">{step.title}</h3>
              <p className="text-gray-500 leading-relaxed">{step.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
