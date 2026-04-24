import { useState } from "react";
import { Menu, X, Brain } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);

  const links = [
    { label: "Services", href: "#services" },
    { label: "How It Works", href: "#how-it-works" },
    { label: "Specialties", href: "#specialties" },
    { label: "Pricing", href: "#pricing" },
    { label: "FAQ", href: "#faq" },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-gray-950/90 backdrop-blur-md border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <a href="#" className="flex items-center gap-2">
            <div className="bg-blue-600 rounded-lg p-1.5">
              <Brain className="h-5 w-5 text-white" />
            </div>
            <span className="text-white font-bold text-lg">MediAI</span>
          </a>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-6">
            {links.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="text-gray-400 hover:text-white text-sm transition-colors"
              >
                {link.label}
              </a>
            ))}
          </div>

          {/* CTA */}
          <div className="hidden md:flex items-center gap-3">
            <Button variant="ghost" size="sm" className="text-gray-300 hover:text-white hover:bg-white/10">
              Sign In
            </Button>
            <Button size="sm">Get Started Free</Button>
          </div>

          {/* Mobile toggle */}
          <button
            className="md:hidden text-gray-400 hover:text-white"
            onClick={() => setIsOpen(!isOpen)}
            aria-label="Toggle menu"
          >
            {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {isOpen && (
        <div className="md:hidden bg-gray-950 border-t border-white/10 px-4 pt-4 pb-6 space-y-3">
          {links.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="block text-gray-400 hover:text-white py-2 text-sm transition-colors"
              onClick={() => setIsOpen(false)}
            >
              {link.label}
            </a>
          ))}
          <div className="pt-3 flex flex-col gap-2">
            <Button variant="ghost" size="sm" className="w-full text-gray-300 hover:text-white hover:bg-white/10 justify-center">
              Sign In
            </Button>
            <Button size="sm" className="w-full">Get Started Free</Button>
          </div>
        </div>
      )}
    </nav>
  );
}
