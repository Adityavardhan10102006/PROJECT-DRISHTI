/**
 * src/App.jsx — Project DRISHTI
 * Minimal + Intelligent + Premium Cybercrime Intelligence Platform.
 *
 * Ministry of Home Affairs | Cybercrime Intelligence Framework
 */

import React, { useState, useEffect } from "react";
import "./App.css";
import { fetchHealth, logout } from "./api.js";
import { isAuthenticated, getUser, clearToken } from "./auth.js";

// Core View Components
import SidebarNav from "./components/SidebarNav.jsx";
import CommandCenterView from "./components/CommandCenterView.jsx";
import CasesListView from "./components/CasesListView.jsx";
import CaseDetailView from "./components/CaseDetailView.jsx";
import SettingsView from "./components/SettingsView.jsx";
import BackendOfflineBanner from "./components/BackendOfflineBanner.jsx";
import LoginPage from "./LoginPage.jsx";
import GarudaDrishtiIcon from "./components/GarudaDrishtiIcon.jsx";

function LogoutIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  );
}

export default function App() {
  // ── Auth State ───────────────────────────────────────────────
  const [authed, setAuthed] = useState(() => isAuthenticated());
  const [currentUser, setCurrentUser] = useState(() => authed ? getUser() : null);
  const [sessionExpired, setSessionExpired] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  // ── Layout & View State ──────────────────────────────────────
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState("overview"); // overview | cases | case_detail | settings
  const [selectedCaseId, setSelectedCaseId] = useState("DR-2026-1001");
  const [apiOnline, setApiOnline] = useState(true);

  // ── Case Selection Handler ──────────────────────────────────
  const handleSelectCase = (caseId) => {
    setSelectedCaseId(caseId);
    setActiveTab("case_detail");
  };

  // ── Backend Health Polling & Offline Event Listeners ────────
  useEffect(() => {
    const checkApi = async () => {
      try {
        await fetchHealth();
        setApiOnline(true);
      } catch {
        setApiOnline(false);
      }
    };
    checkApi();
    const interval = setInterval(checkApi, 25000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleOnline = () => setApiOnline(true);
    const handleOffline = () => setApiOnline(false);
    const handleExpired = () => {
      setSessionExpired(true);
      setAuthed(false);
      setCurrentUser(null);
    };

    window.addEventListener("drishti:network-online", handleOnline);
    window.addEventListener("drishti:network-offline", handleOffline);
    window.addEventListener("drishti:session-expired", handleExpired);

    return () => {
      window.removeEventListener("drishti:network-online", handleOnline);
      window.removeEventListener("drishti:network-offline", handleOffline);
      window.removeEventListener("drishti:session-expired", handleExpired);
    };
  }, []);

  // ── Auth Action Handlers ─────────────────────────────────────
  const handleLoginSuccess = (userData) => {
    setAuthed(true);
    setCurrentUser(userData || getUser());
    setSessionExpired(false);
  };

  const handleLogout = async () => {
    setLoggingOut(true);
    try {
      await logout();
    } catch {
      clearToken();
    } finally {
      setAuthed(false);
      setCurrentUser(null);
      setLoggingOut(false);
    }
  };

  // ── Unauthenticated State: Show Login ────────────────────────
  if (!authed) {
    return (
      <LoginPage
        onLoginSuccess={handleLoginSuccess}
        sessionExpired={sessionExpired}
      />
    );
  }

  // ── Authenticated Intelligence Shell ─────────────────────────
  return (
    <div className="app-shell">
      {/* Backend Offline Warning Banner */}
      <BackendOfflineBanner />

      {/* ── TOP NAV (Compact 50px) ─────────────────────────── */}
      <header className="topnav">
        <div className="topnav-brand">
          <GarudaDrishtiIcon size={24} glow />
          <div className="topnav-title-group">
            <span className="topnav-title">DRISHTI</span>
            <span className="topnav-subtitle">Predictive Cybercrime Intelligence</span>
          </div>
          <span className="intel-badge" style={{ borderColor: "rgba(229, 9, 20, 0.35)", color: "var(--text-primary)" }}>
            CASE INTELLIGENCE
          </span>
        </div>

        <div className="topnav-actions">
          {/* Status Indicator */}
          <div className="status-pill-system">
            <span
              className="status-dot"
              style={{
                background: apiOnline ? "var(--risk-low)" : "var(--risk-high)",
              }}
            />
            <span>{apiOnline ? "Operational" : "Service Offline"}</span>
          </div>

          {/* User Profile + Logout */}
          <div className="user-badge">
            <span>{currentUser?.username || "Analyst"}</span>
          </div>

          <button
            type="button"
            className="btn-signout"
            onClick={handleLogout}
            disabled={loggingOut}
            title="Sign out of DRISHTI"
          >
            <LogoutIcon />
            <span>{loggingOut ? "..." : "Sign Out"}</span>
          </button>
        </div>
      </header>

      {/* ── APP BODY: SIDEBAR + WORKSPACE ───────────────────── */}
      <div className="app-body">
        <SidebarNav
          activeTab={activeTab}
          onNavigate={(tab) => setActiveTab(tab)}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          activeCaseCount={5}
        />

        {/* Dynamic Workspace */}
        <main className="main-workspace">
          {activeTab === "overview" && (
            <CommandCenterView
              onSelectCase={handleSelectCase}
              onNavigate={(tab) => setActiveTab(tab)}
            />
          )}

          {activeTab === "cases" && (
            <CasesListView onSelectCase={handleSelectCase} />
          )}

          {activeTab === "case_detail" && (
            <CaseDetailView
              caseId={selectedCaseId}
              onBack={() => setActiveTab("cases")}
            />
          )}

          {activeTab === "settings" && <SettingsView />}
        </main>
      </div>
    </div>
  );
}
