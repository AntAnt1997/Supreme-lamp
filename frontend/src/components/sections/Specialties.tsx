const specialties = [
  { name: "General Medicine", icon: "🏥", count: "500+ conditions" },
  { name: "Mental Health", icon: "🧠", count: "200+ conditions" },
  { name: "Cardiology", icon: "❤️", count: "150+ conditions" },
  { name: "Pediatrics", icon: "👶", count: "300+ conditions" },
  { name: "Dermatology", icon: "🔬", count: "400+ conditions" },
  { name: "Nutrition", icon: "🥗", count: "100+ plans" },
  { name: "Orthopedics", icon: "🦴", count: "200+ conditions" },
  { name: "Neurology", icon: "⚡", count: "180+ conditions" },
];

export default function Specialties() {
  return (
    <section id="specialties" className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <p className="text-blue-600 font-semibold text-sm uppercase tracking-wider mb-3">
            Coverage
          </p>
          <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
            Medical Specialties We Cover
          </h2>
          <p className="text-xl text-gray-500 max-w-2xl mx-auto">
            Our AI workers are trained across a wide range of medical disciplines to provide comprehensive support.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {specialties.map((specialty) => (
            <div
              key={specialty.name}
              className="group flex flex-col items-center text-center p-6 rounded-2xl border border-gray-100 bg-white hover:border-blue-200 hover:bg-blue-50 hover:shadow-md transition-all duration-300 cursor-pointer"
            >
              <span className="text-4xl mb-3">{specialty.icon}</span>
              <h3 className="font-semibold text-gray-900 text-sm mb-1 group-hover:text-blue-700">{specialty.name}</h3>
              <p className="text-xs text-gray-400">{specialty.count}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
