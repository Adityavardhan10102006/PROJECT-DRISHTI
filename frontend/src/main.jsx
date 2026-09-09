import React, { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";

// Polyfill React.use for React 18 compatibility with modern libraries
if (!React.use) {
  React.use = function (usable) {
    if (usable && (usable._currentValue !== undefined || usable.$$typeof)) {
      return React.useContext(usable);
    }
    return usable;
  };
}

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
