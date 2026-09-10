import React from "react";

/**
 * GarudaDrishtiIcon — Official Vector Emblem of PROJECT DRISHTI
 * Combines:
 *   - GARUDA: Vigilance, strength, speed, aerial & strategic awareness (swept wings)
 *   - DRISHTI: Vision, foresight, prediction, cyber intelligence (central eye & iris)
 *   - TARGET: Precision cashout interception coordinates (reticle crosshair & beacon)
 */
export default function GarudaDrishtiIcon({
  size = 28,
  className = "",
  glow = false,
  color = "var(--red-primary, #E50914)",
  accentColor = "var(--red-bright, #FF2B35)",
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`garuda-drishti-icon ${className}`}
      style={{
        display: "inline-block",
        verticalAlign: "middle",
        filter: glow ? `drop-shadow(0 0 8px ${color})` : "none",
        transition: "filter 0.2s ease, transform 0.2s ease",
        flexShrink: 0,
      }}
      aria-label="DRISHTI Garuda Symbol"
    >
      <defs>
        <linearGradient id="garudaWingGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={accentColor} />
          <stop offset="60%" stopColor={color} />
          <stop offset="100%" stopColor="#8B0E16" />
        </linearGradient>
        <radialGradient id="drishtiIrisGrad" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#FFF" />
          <stop offset="45%" stopColor={accentColor} />
          <stop offset="100%" stopColor={color} />
        </radialGradient>
      </defs>

      {/* ── 1. GARUDA WINGS (Swept-back vigilant aerial wings) ── */}
      {/* Left Wing Outer Tier */}
      <path
        d="M24 14C19 9 12 7 4 10C8 16 13 18 19 19L24 14Z"
        fill="url(#garudaWingGrad)"
        opacity="0.95"
      />
      {/* Left Wing Inner Feather */}
      <path
        d="M22 17C17 14 11 13 6 15C9 19 14 20 19 21L22 17Z"
        fill={color}
        opacity="0.8"
      />

      {/* Right Wing Outer Tier */}
      <path
        d="M24 14C29 9 36 7 44 10C40 16 35 18 29 19L24 14Z"
        fill="url(#garudaWingGrad)"
        opacity="0.95"
      />
      {/* Right Wing Inner Feather */}
      <path
        d="M26 17C31 14 37 13 42 15C39 19 34 20 29 21L26 17Z"
        fill={color}
        opacity="0.8"
      />

      {/* ── 2. DRISHTI EYE (Predictive Vision Almond Contour) ── */}
      <path
        d="M8 24C12 18 18 15 24 15C30 15 36 18 40 24C36 30 30 33 24 33C18 33 12 30 8 24Z"
        stroke={accentColor}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="#12151B"
      />

      {/* Inner Iris Ring */}
      <circle
        cx="24"
        cy="24"
        r="5.5"
        stroke={color}
        strokeWidth="1.5"
        fill="url(#drishtiIrisGrad)"
      />

      {/* Pupil Core */}
      <circle cx="24" cy="24" r="2.2" fill="#08090C" />
      <circle cx="25" cy="23" r="0.8" fill="#FFFFFF" opacity="0.9" />

      {/* ── 3. TARGETING CROSSHAIRS & FOCAL BEACON ── */}
      {/* Reticle Vertical Ticks */}
      <line x1="24" y1="9" x2="24" y2="13" stroke={accentColor} strokeWidth="1.8" strokeLinecap="round" />
      <line x1="24" y1="35" x2="24" y2="40" stroke={accentColor} strokeWidth="1.8" strokeLinecap="round" />

      {/* Reticle Horizontal Ticks */}
      <line x1="2" y1="24" x2="6" y2="24" stroke={accentColor} strokeWidth="1.8" strokeLinecap="round" />
      <line x1="42" y1="24" x2="46" y2="24" stroke={accentColor} strokeWidth="1.8" strokeLinecap="round" />

      {/* Ground Interception Pin / Apex Talon */}
      <path
        d="M21 37L24 43L27 37"
        stroke={accentColor}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
