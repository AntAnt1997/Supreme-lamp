import { Brain } from "lucide-react";

export default function Footer() {
  const footerLinks = {
    Product: ["Features", "Pricing", "Security", "Integrations"],
    Company: ["About", "Blog", "Careers", "Press"],
    Support: ["Help Center", "Contact", "Privacy Policy", "Terms of Service"],
    Specialties: ["General Medicine", "Mental Health", "Cardiology", "Pediatrics"],
  };

  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-8">
          {/* Brand */}
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 text-white font-bold text-xl mb-4">
              <Brain className="h-7 w-7 text-blue-400" />
              <span>MediAI</span>
            </div>
            <p className="text-sm leading-relaxed text-gray-400">
              AI-powered medical workers available 24/7 to support your health journey.
            </p>
          </div>

          {/* Links */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h3 className="text-white font-semibold mb-4">{category}</h3>
              <ul className="space-y-2">
                {links.map((link) => (
                  <li key={link}>
                    <a href="#" className="text-sm text-gray-400 hover:text-white transition-colors">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 pt-8 border-t border-gray-800">
          {/* Medical Disclaimer */}
          <div className="bg-gray-800 rounded-lg p-4 mb-6">
            <p className="text-xs text-gray-400 text-center leading-relaxed">
              ⚠️ <strong className="text-gray-300">Medical Disclaimer:</strong> MediAI is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition. In case of emergency, call 911 immediately.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <p className="text-sm text-gray-500">
              © {new Date().getFullYear()} MediAI. All rights reserved.
            </p>
            <div className="flex gap-4 text-sm text-gray-500">
              <a href="#" className="hover:text-white transition-colors">Privacy</a>
              <a href="#" className="hover:text-white transition-colors">Terms</a>
              <a href="#" className="hover:text-white transition-colors">HIPAA</a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
