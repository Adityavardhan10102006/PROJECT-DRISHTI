import React from "react";

function OverviewIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" />
      <rect x="14" y="3" width="7" height="7" />
      <rect x="14" y="14" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" />
    </svg>
  );
}

function CasesIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
    { id: "settings", label: "Settings", icon: <SettingsIcon /> },
  ];

  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""} ${mobileOpen ? "mobile-open" : ""}`}>
      {/* Sidebar Header */}
      <div className="sidebar-header">
        {!collapsed && (
          <div className="sidebar-brand-group">
            <span className="sidebar-brand-title">DRISHTI</span>
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
                      <span className="badge-tag badge-risk-medium" style={{ marginLeft: "auto", fontSize: "10px", padding: "1px 5px" }}>
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
              <span style={{ textTransform: "uppercase", letterSpacing: "0.5px" }}>SYSTEM</span>
              <span style={{ color: "var(--risk-low)", display: "inline-flex", alignItems: "center", gap: "4px" }}>
                <span className="status-dot" style={{ width: "5px", height: "5px" }}></span> Operational
              </span>
            </div>
            <div className="sidebar-footer-row" style={{ marginTop: "4px" }}>
              <span>ROLE</span>
              <span style={{ color: "var(--text-secondary)" }}>Analyst</span>
            </div>
          </>
        ) : (
          <div style={{ textAlign: "center" }} title="System Operational · Analyst">
            <span className="status-dot" style={{ width: "6px", height: "6px", background: "var(--risk-low)", display: "inline-block" }}></span>
          </div>
        )}
      </div>
    </aside>
  );
}
