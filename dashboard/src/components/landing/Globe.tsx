import { useMemo } from "react";

// CSS-based 3D globe with animated rings — lightweight, no WebGL dependency
// Inspired by Aceternity UI's Globe component

const BENGALURU_ARCS = [
  { from: [12.97, 77.59], to: [12.91, 77.64], label: "Central → South" },
  { from: [12.97, 77.59], to: [12.97, 77.75], label: "Central → Whitefield" },
  { from: [12.91, 77.64], to: [12.84, 77.66], label: "South → Electronic City" },
  { from: [12.97, 77.59], to: [12.99, 77.55], label: "Central → Hebbal" },
  { from: [12.88, 77.60], to: [12.91, 77.64], label: "JP Nagar → Koramangala" },
  { from: [12.96, 77.75], to: [12.91, 77.64], label: "Whitefield → HSR" },
];

function latLngToSpherical(
  lat: number,
  lng: number,
  radius: number
): { x: number; y: number; z: number } {
  const phi = ((90 - lat) * Math.PI) / 180;
  const theta = ((lng + 180) * Math.PI) / 180;
  return {
    x: -(radius * Math.sin(phi) * Math.cos(theta)),
    y: radius * Math.cos(phi),
    z: radius * Math.sin(phi) * Math.sin(theta),
  };
}

export function Globe() {
  // Generate "country" dot outlines (simplified grid of dots for visual effect)
  const gridDots = useMemo(() => {
    const dots: { x: number; y: number; opacity: number }[] = [];
    const r = 140;
    for (let lat = -80; lat <= 80; lat += 12) {
      for (let lng = -180; lng <= 180; lng += 14) {
        const s = latLngToSpherical(lat, lng, r);
        // Only show dots on the front hemisphere
        if (s.z > 0) {
          const brightness = s.z / r;
          dots.push({
            x: 50 + (s.x / r) * 42,
            y: 50 - (s.y / r) * 42,
            opacity: 0.15 + brightness * 0.5,
          });
        }
      }
    }
    return dots;
  }, []);

  // Project arcs onto front face
  const arcs = useMemo(() => {
    return BENGALURU_ARCS.map((arc) => {
      const from = latLngToSpherical(arc.from[0], arc.from[1], 140);
      const to = latLngToSpherical(arc.to[0], arc.to[1], 140);
      const visible = from.z > -40 || to.z > -40;
      return {
        x1: 50 + (from.x / 140) * 42,
        y1: 50 - (from.y / 140) * 42,
        x2: 50 + (to.x / 140) * 42,
        y2: 50 - (to.y / 140) * 42,
        visible,
      };
    });
  }, []);

  return (
    <div className="relative w-[500px] h-[500px] md:w-[600px] md:h-[600px]">
      {/* Atmosphere glow */}
      <div className="absolute inset-0 rounded-full bg-brand/[0.03] blur-3xl" />
      <div className="absolute inset-[5%] rounded-full bg-brand/[0.02] blur-2xl" />

      {/* Globe sphere */}
      <div className="absolute inset-[10%] rounded-full border border-brand/10 bg-[#0a0e18] overflow-hidden shadow-[0_0_80px_rgba(59,130,246,0.06)]">
        {/* Inner radial gradient */}
        <div className="absolute inset-0 rounded-full bg-[radial-gradient(circle_at_40%_35%,rgba(59,130,246,0.06)_0%,transparent_60%)]" />

        {/* Grid dots */}
        <svg viewBox="0 0 100 100" className="absolute inset-0 w-full h-full">
          {gridDots.map((dot, i) => (
            <circle
              key={i}
              cx={dot.x}
              cy={dot.y}
              r={0.35}
              fill="#3b82f6"
              opacity={dot.opacity}
            />
          ))}
        </svg>

        {/* Arcs */}
        <svg viewBox="0 0 100 100" className="absolute inset-0 w-full h-full">
          <defs>
            <linearGradient id="arc-grad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.6} />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.1} />
            </linearGradient>
          </defs>
          {arcs
            .filter((a) => a.visible)
            .map((arc, i) => (
              <line
                key={i}
                x1={arc.x1}
                y1={arc.y1}
                x2={arc.x2}
                y2={arc.y2}
                stroke="url(#arc-grad)"
                strokeWidth={0.25}
                className="animate-pulse"
                style={{ animationDelay: `${i * 0.4}s`, animationDuration: "3s" }}
              />
            ))}
          {/* Node points at arc endpoints */}
          {arcs
            .filter((a) => a.visible)
            .flatMap((arc, i) => [
              <circle
                key={`a-${i}`}
                cx={arc.x1}
                cy={arc.y1}
                r={0.6}
                fill="#3b82f6"
                opacity={0.8}
              />,
              <circle
                key={`b-${i}`}
                cx={arc.x2}
                cy={arc.y2}
                r={0.6}
                fill="#3b82f6"
                opacity={0.8}
              />,
            ])}
        </svg>
      </div>

      {/* Rotating ring 1 */}
      <div
        className="absolute inset-[5%] rounded-full border border-brand/8 animate-spin-slow"
        style={{ transformOrigin: "center" }}
      />

      {/* Rotating ring 2 */}
      <div
        className="absolute inset-[2%] rounded-full border border-brand/[0.04]"
        style={{
          transform: "rotateX(75deg) rotateZ(120deg)",
          transformOrigin: "center",
          animation: "spin-slow 30s linear infinite reverse",
        }}
      />

      {/* Orbiting dot */}
      <div
        className="absolute inset-[5%]"
        style={{ animation: "spin-slow 15s linear infinite", transformOrigin: "center" }}
      >
        <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 h-2 w-2 rounded-full bg-brand shadow-[0_0_12px_rgba(59,130,246,0.6)]" />
      </div>
    </div>
  );
}
