import { BrowserRouter, Routes, Route } from "react-router-dom";
import LandingPage from "@/pages/LandingPage";
import Home from "@/pages/Home";
import WalletTracker from "@/pages/WalletTracker";
import NotFound from "@/pages/NotFound";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/app" element={<Home />} />
        <Route path="/wallets" element={<WalletTracker />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
