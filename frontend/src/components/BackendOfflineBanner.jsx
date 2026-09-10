import React, { useState, useEffect } from "react";
import { fetchHealth } from "../api.js";

export default function BackendOfflineBanner() {
  const [isOffline, setIsOffline] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const [lastChecked, setLastChecked] = useState(null);

  const checkConnectivity = async () => {
    setRetrying(true);
    try {
      await fetchHealth();
      setIsOffline(false);
      setLastChecked(new Date().toLocaleTimeString());
    } catch {
      setIsOffline(true);
      setLastChecked(new Date().toLocaleTimeString());
    } finally {
      setRetrying(false);
    }
  };

  useEffect(() => {
    const handleOffline = () => setIsOffline(true);
    const handleOnline = () => setIsOffline(false);

    window.addEventListener("drishti:network-offline", handleOffline);
    window.addEventListener("drishti:network-online", handleOnline);

    // Initial check
    checkConnectivity();

    // Heartbeat check every 15s
    const interval = setInterval(checkConnectivity, 15000);

    return () => {
      window.removeEventListener("drishti:network-offline", handleOffline);
      window.removeEventListener("drishti:network-online", handleOnline);
      clearInterval(interval);
    };
  }, []);

  if (!isOffline) return null;

  return (
    <div className="backend-offline-banner">
      <div className="offline-content">
        <span className="offline-pulse"></span>
        <div className="offline-text">
          <strong>BACKEND DISCONNECTED (127.0.0.1:8000)</strong>
          <span> — DRISHTI intelligence services unreachable. Showing cached/local interface state. {lastChecked && `(Checked: ${lastChecked})`}</span>
        </div>
      </div>
      <div className="offline-actions">
        <button
          className="btn-retry-offline"
          onClick={checkConnectivity}
          disabled={retrying}
        >
          {retrying ? "Pinging Engine..." : "🔄 Retry Connection"}
        </button>
      </div>
    </div>
  );
}
