import React from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { DesktopHome } from "./pages/DesktopHome";
import { MobileScanner } from "./pages/MobileScanner";

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DesktopHome />} />
        <Route path="/scan/:sessionId" element={<MobileScanner />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
