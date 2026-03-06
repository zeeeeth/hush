export interface Station {
  id: string;
  lat: number;
  lng: number;
}

export interface RouteStep {
  type: "transit" | "walk";
  // transit-only fields
  line?: string;
  color?: string;
  departure?: string;
  arrival?: string;
  intermediate_stops?: string[];
  num_stops?: number;
  // walk-only fields
  distance_m?: number;
  duration_min: number;
}

export interface Route {
  duration_min: number;
  distance_km: number;
  quiet_score: number | null;
  is_recommended: boolean;
  steps: RouteStep[];
}

export interface RoutesResponse {
  routes: Route[];
  prediction_window: {
    from: string;
    to: string;
  };
}
