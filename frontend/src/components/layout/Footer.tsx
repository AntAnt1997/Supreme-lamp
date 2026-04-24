import { Brain } from "lucide-react";

export default function Footer() {
  const year = new Date().getFullYear();

  const cols = [
    {
      heading: "Product",
      links: ["Features", "Pricing", "Security", "Changelog"],
    },
    {
      heading: "Company",
      links: ["About", "Blog", "Careers", "Press"],
    },
    {
      heading: "Legal",
      links: ["Privacy Policy", "Terms of Service", "HIPAA Compliance", "Cookie Policy"],
    },
  ];

  return (
    <footer className="bg-gray-950 border-t border-white/10 text-gray-400">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="bg-blue-600 rounded-lg p-1.5">
                <Brain className="h-5 w-5 text-white" />
              </div>
              <span className="text-white font-bold text-lg">MediAI</span>
            </div>
            <p className="text-sm leading-relaxed">
              AI-powered medical workers available 24/7 to support your health journey.
            </p>
          </div>

          {/* Link columns */}
          {cols.map((col) => (
            <div key={col.heading}>
              <h3 className="text-white font-semibold mb-4 text-sm">{col.heading}</h3>
              <ul className="space-y-2">
                {col.links.map((link) => (
                  <li key={link}>
                    <a href="#" className="text-sm hover:text-white transition-colors">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="mt-12 pt-8 border-t border-white/10">
          <p className="text-xs text-center text-gray-500">
            &copy; {year} MediAI. All rights reserved.
          </p>
          <p className="text-xs text-center text-gray-600 mt-2 max-w-2xl mx-auto">
            ⚠️ <strong>Medical Disclaimer:</strong> MediAI is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.
          </p>
        </div>
      </div>
    </footer>
  );
}
