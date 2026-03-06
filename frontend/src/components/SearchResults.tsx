import type { RoutesResponse } from "../types";
import { RouteCard } from "./RouteCard";

interface Props {
  data: RoutesResponse | undefined;
  error: Error | null;
  isLoading: boolean;
  searched: boolean;
  originName: string;
  destinationName: string;
}

export function SearchResults({
  data,
  error,
  isLoading,
  searched,
  originName,
  destinationName,
}: Props) {
  if (!searched) return null;

  if (originName === destinationName) {
    return <div className="error-card">Select different stations</div>;
  }

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-train">🚇</div>
        <div className="loading-dots">
          <div className="loading-dot" />
          <div className="loading-dot" />
          <div className="loading-dot" />
        </div>
        <div className="loading-text">Analyzing routes...</div>
        <div className="loading-subtext">Predicting congestion for the next hour</div>
      </div>
    );
  }

  if (error) {
    return <div className="error-card">❌ {error.message}</div>;
  }

  if (!data || data.routes.length === 0) {
    return <div className="error-card">No routes found</div>;
  }

  const { routes, prediction_window } = data;
  const fromTime = new Date(prediction_window.from).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
  const toTime = new Date(prediction_window.to).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
  const bestIdx = routes.findIndex((r) => r.is_recommended);

  return (
    <>
      <div className="prediction-banner">
        <span className="prediction-icon">🔮</span>
        <div className="prediction-text">
          <div className="prediction-label">AI Congestion Forecast</div>
          <div className="prediction-time">
            {fromTime} → {toTime}
          </div>
          <div className="prediction-hint">
            Scores reflect predicted crowding for the next hour
          </div>
        </div>
      </div>

      <div className="results-header">
        {routes.length} route{routes.length > 1 ? "s" : ""} found · Route{" "}
        {bestIdx + 1} recommended
      </div>

      {routes.map((route, i) => (
        <RouteCard key={i} route={route} isBest={i === bestIdx} />
      ))}
    </>
  );
}
