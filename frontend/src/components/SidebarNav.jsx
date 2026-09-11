import React from "react";
import GarudaDrishtiIcon from "./GarudaDrishtiIcon.jsx";

function OverviewIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" />
      <rect x="14" y="3" width="7" height="7" />
      <rect x="14" y="14" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" />
    </svg>
  );
}

function CasesIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
    </svg>
  );
}

function PipelineIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="22" y1="12" x2="18" y2="12" />
      <line x1="6" y1="12" x2="2" y2="12" />
      <line x1="12" y1="6" x2="12" y2="2" />
      <line x1="12" y1="22" x2="12" y2="18" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function TrustIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <polyline points="9 12 11 14 15 10" />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  );
}

export default function SidebarNav({
  activeTab,
  onNavigate,
  collapsed,
  onToggleCollapse,
  activeCaseCount = 5,
  mobileOpen = false,
}) {
  const navItems = [
    { id: "overview", label: "Overview", icon: <OverviewIcon /> },
    {
      id: "cases",
      label: "Cases",
      icon: <CasesIcon />,
      badge: activeCaseCount > 0 ? activeCaseCount : null,
    },
    { id: "pipeline", label: "Intelligence Pipeline", icon: <PipelineIcon /> },
    { id: "data-trust", label: "Data & Trust", icon: <TrustIcon /> },
    { id: "settings", label: "Settings", icon: <SettingsIcon /> },
  ];

  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""} ${mobileOpen ? "mobile-open" : ""}`}>
      {/* Sidebar Header */}
      <div className="sidebar-header">
        {!collapsed ? (
          <div className="sidebar-brand-group" style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <GarudaDrishtiIcon size={28} glow />
            <div style={{ display: "flex", flexDirection: "column" }}>
              <span className="sidebar-brand-title" style={{ fontSize: "16px", fontWeight: "700", letterSpacing: "1px", color: "var(--text-primary)" }}>
                DRISHTI
              </span>
              <span style={{ fontSize: "9.5px", color: "var(--text-muted)", letterSpacing: "0.4px", textTransform: "uppercase" }}>
                Cyber Intelligence
              </span>
            </div>
          </div>
        ) : (
          <div style={{ display: "flex", justifyContent: "center", width: "100%" }}>
            <GarudaDrishtiIcon size={24} />
          </div>
        )}
        <button
          className="sidebar-collapse-btn"
          onClick={onToggleCollapse}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? "→" : "←"}
        </button>
      </div>

      {/* Navigation Items */}
      <ul className="sidebar-nav-list">
        {navItems.map((item) => {
          const isActive =
            activeTab === item.id ||
            (item.id === "cases" && activeTab === "case_detail");
          return (
            <li key={item.id}>
              <button
                className={`nav-item-btn ${isActive ? "active" : ""}`}
                onClick={() => onNavigate(item.id)}
                title={collapsed ? item.label : ""}
              >
                <span className="nav-icon">{item.icon}</span>
                {!collapsed && (
                  <>
                    <span>{item.label}</span>
                    {item.badge && (
                      <span className="badge-tag" style={{ marginLeft: "auto", fontSize: "10px", padding: "1px 6px", background: "rgba(229,9,20,0.15)", color: "var(--red-bright)", border: "1px solid rgba(229,9,20,0.3)" }}>
                        {item.badge}
                      </span>
                    )}
                  </>
                )}
              </button>
            </li>
          );
        })}
      </ul>

      {/* Sidebar Footer */}
      <div className="sidebar-footer">
        {!collapsed ? (
          <>
            <div className="sidebar-footer-row">
              <span style={{ textTransform: "uppercase", letterSpacing: "0.5px", fontSize: "10.5px", color: "var(--text-muted)" }}>SYSTEM</span>
              <span style={{ color: "var(--success)", display: "inline-flex", alignItems: "center", gap: "5px", fontSize: "11px", fontWeight: 600 }}>
                <span className="status-dot" style={{ width: "5px", height: "5px", background: "var(--success)" }}></span> Operational
              </span>
            </div>
            <div className="sidebar-footer-row" style={{ marginTop: "4px", fontSize: "10px", color: "var(--text-muted)" }}>
              <span>ENV</span>
              <span>Demo · Synthetic</span>
            </div>
            <div className="sidebar-footer-row" style={{ marginTop: "8px", paddingTop: "8px", borderTop: "1px solid var(--border)", fontSize: "11.5px" }}>
              <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                <span style={{ color: "var(--text-secondary)" }}>Analyst</span>
              </span>
              <span style={{ fontSize: "9.5px", padding: "1px 5px", background: "rgba(229,9,20,0.15)", border: "1px solid rgba(229,9,20,0.3)", borderRadius: "2px", color: "var(--red-bright)", fontFamily: "var(--font-mono)" }}>MHA-AUTH</span>
            </div>
          </>
        ) : (
          <div style={{ textAlign: "center" }} title="System Operational · Analyst">
            <span className="status-dot" style={{ width: "6px", height: "6px", background: "var(--success)", display: "inline-block" }}></span>
          </div>
        )}
      </div>
    </aside>
  );
}
