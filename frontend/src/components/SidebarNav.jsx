import React, { useState } from "react";

export default function SidebarNav({
  activeTab,
  onNavigate,
  collapsed,
  onToggleCollapse,
  activeAlertCount = 0,
  activeCaseCount = 0,
  userRole = "analyst",
}) {
  const sections = [
    {
      title: "COMMAND",
      items: [
        { id: "command_center", label: "Command Center", icon: "📊", badge: null },
      ],
    },
    {
      title: "INVESTIGATIONS",
      items: [
        { id: "cases", label: "Case Directory", icon: "📁", badge: activeCaseCount > 0 ? activeCaseCount : null },
        { id: "trail", label: "Money Trail Graph", icon: "🕸️", badge: null },
      ],
    },
    {
      title: "INTELLIGENCE",
      items: [
        { id: "prediction", label: "5D Predictions", icon: "⚡", badge: "AI" },
        { id: "map", label: "Tactical GIS Map", icon: "🗺️", badge: null },
        { id: "alerts", label: "Alert Matrix", icon: "🚨", badge: activeAlertCount > 0 ? activeAlertCount : null, badgeClass: "badge-red" },
      ],
    },
    {
      title: "OPERATIONS",
      items: [
        { id: "operations", label: "Field Operations", icon: "🚔", badge: null },
      ],
    },
    {
      title: "ANALYTICS & AI",
      items: [
        { id: "models", label: "Model Intelligence", icon: "📈", badge: "v2.2" },
        ...(userRole === "admin" || userRole === "analyst"
          ? [{ id: "audit", label: "Security Audit Log", icon: "📋", badge: null }]
          : []),
      ],
    },
    {
      title: "SYSTEM",
      items: [
        { id: "status", label: "System Status", icon: "🛡️", badge: null },
        { id: "about", label: "Architecture & About", icon: "ℹ️", badge: null },
      ],
    },
  ];

  return (
    <aside className={`sidebar-nav ${collapsed ? "sidebar-collapsed" : ""}`}>
      {/* Sidebar Header / Brand Toggle */}
      <div className="sidebar-header">
        {!collapsed && (
          <div className="sidebar-brand-group">
            <span className="sidebar-brand-title">DRISHTI SOC</span>
            <span className="sidebar-brand-tag">MHA INTELLIGENCE</span>
          </div>
        )}
        <button
          className="sidebar-collapse-btn"
          onClick={onToggleCollapse}
          title={collapsed ? "Expand Navigation Sidebar" : "Collapse Sidebar"}
          aria-label={collapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          {collapsed ? "▶" : "◀"}
        </button>
      </div>

      {/* Navigation Sections */}
      <div className="sidebar-menu">
        {sections.map((sec, secIdx) => (
          <div key={secIdx} className="sidebar-section">
            {!collapsed && <div className="sidebar-section-title">{sec.title}</div>}
            <div className="sidebar-section-items">
              {sec.items.map((item) => {
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    className={`sidebar-item-btn ${isActive ? "active" : ""}`}
                    onClick={() => onNavigate(item.id)}
                    title={collapsed ? `${item.label}` : ""}
                  >
                    <span className="sidebar-item-icon">{item.icon}</span>
                    {!collapsed && (
                      <>
                        <span className="sidebar-item-label">{item.label}</span>
                        {item.badge && (
                          <span className={`sidebar-item-badge ${item.badgeClass || ""}`}>
                            {item.badge}
                          </span>
                        )}
                      </>
                    )}
                    {collapsed && item.badge && (
                      <span className="sidebar-collapsed-dot"></span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Sidebar Footer */}
      <div className="sidebar-footer">
        {!collapsed ? (
          <div className="sidebar-footer-content">
            <span className="soc-live-badge">
              <span className="soc-dot"></span> SOC ACTIVE
            </span>
            <span className="soc-version">SIH26184 · v2.2</span>
          </div>
        ) : (
          <div className="sidebar-footer-collapsed" title="SOC Active • SIH26184">
            <span className="soc-dot"></span>
          </div>
        )}
      </div>
    </aside>
  );
}
