import type { Route } from "../types";

interface Props {
  route: Route;
  isBest: boolean;
}

export function RouteCard({ route, isBest }: Props) {
  const { duration_min, distance_km, steps, quiet_score } = route;

  const transitCount = steps.filter((s) => s.type === "transit").length;
  const transfers = Math.max(0, transitCount - 1);
  const transferText = transfers === 0 ? "Direct" : `${transfers} transfer${transfers > 1 ? "s" : ""}`;

  // Quiet score badge
  let quietBadge: React.ReactNode;
  if (quiet_score !== null && quiet_score !== undefined) {
    if (quiet_score >= 7) {
      quietBadge = <span className="quiet-badge-good">• Quiet {quiet_score}/10</span>;
    } else if (quiet_score >= 4) {
      quietBadge = <span className="quiet-badge-pending">• Moderate {quiet_score}/10</span>;
    } else {
      quietBadge = <span className="quiet-badge-bad">• Busy {quiet_score}/10</span>;
    }
  } else {
    quietBadge = <span className="quiet-badge-pending">○ Score pending</span>;
  }

  return (
    <div className={`route-card${isBest ? " route-card-best" : ""}`}>
      {isBest && <span className="best-route-badge">✨ QUIETEST</span>}

      <div className="route-header">
        <div style={{ display: "flex", alignItems: "center" }}>
          <span className="duration-badge">{duration_min} min</span>
          <span className="route-meta">
            {distance_km.toFixed(1)} km · {transferText}
          </span>
        </div>
        {quietBadge}
      </div>

      {steps.map((step, i) => {
        if (step.type === "transit") {
          return (
            <div className="step-row" key={i}>
              <span
                className="line-badge"
                style={{ backgroundColor: step.color ?? "#888888" }}
              >
                {step.line}
              </span>
              <span className="step-details">
                {step.departure} → {step.arrival}
              </span>
              <span className="step-meta">
                {step.num_stops} stops · {step.duration_min}m
              </span>
            </div>
          );
        }
        return (
          <div className="step-row" key={i}>
            <span className="walk-icon">→</span>
            <span className="step-details">Walk {step.distance_m}m</span>
            <span className="step-meta">{step.duration_min}m</span>
          </div>
        );
      })}
    </div>
  );
}
