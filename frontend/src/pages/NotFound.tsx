import { Brain } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center text-center px-4">
      <div>
        <div className="flex justify-center mb-6">
          <div className="bg-blue-600 rounded-2xl p-4">
            <Brain className="h-12 w-12 text-white" />
          </div>
        </div>
        <h1 className="text-7xl font-bold text-white mb-4">404</h1>
        <p className="text-xl text-gray-400 mb-8">
          Oops — this page doesn't exist. Let's get you back on track.
        </p>
        <Button size="lg" onClick={() => (window.location.href = "/")}>
          Go to Home
        </Button>
      </div>
    </div>
  );
}
