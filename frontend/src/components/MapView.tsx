import { useMemo } from "react";
import Map from "react-map-gl/maplibre";
import { DeckGL } from "@deck.gl/react";
import { ScatterplotLayer } from "@deck.gl/layers";
import type { Route, Station } from "../types";
import "maplibre-gl/dist/maplibre-gl.css";

interface MarkerPoint {
  name: string;
  lat: number;
  lon: number;
  color: [number, number, number, number];
  radius: number;
}

interface Props {
  originName: string;
  destinationName: string;
  stations: Record<string, Station>;
  bestRoute: Route | null;
  stationCoords: Record<string, { lat: number; lng: number; name: string }>;
}

const MAP_STYLE ="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";
const TIMES_SQUARE_COORDS = { lat: 40.758, lng: -73.9855 };
const GREEN: [number, number, number, number]  = [0, 255, 136, 255];
const RED: [number, number, number, number]    = [255, 68, 68, 255];
const YELLOW: [number, number, number, number] = [250, 204, 21, 255];
const DEFAULT_MARKER_RADIUS = 100;

export function MapView({
  originName,
  destinationName,
  stations,
  bestRoute,
  stationCoords,
}: Props) {
  const { markers, viewState } = useMemo(() => {
    const markers: MarkerPoint[] = [];

    const origin = stations[originName];
    const dest = stations[destinationName];

    // Starting station - Green marker
    if (origin?.lat && origin?.lng) {
      markers.push({
        name: originName,
        lat: origin.lat,
        lon: origin.lng,
        color: GREEN,
        radius: DEFAULT_MARKER_RADIUS,
      });
    }

    // Destination station - Red marker
    if (dest?.lat && dest?.lng) {
      markers.push({
        name: destinationName,
        lat: dest.lat,
        lon: dest.lng,
        color: RED,
        radius: DEFAULT_MARKER_RADIUS,
      });
    }

    // Intermediate stations in the best route - Yellow
    if (bestRoute) {
      const seen = new Set<string>();
      for (const step of bestRoute.steps) {
        if (step.type !== "transit") continue;
        for (const stopName of [step.departure!, step.arrival!]) {
          if (
            stopName.toLowerCase() === originName.toLowerCase() ||
            stopName.toLowerCase() === destinationName.toLowerCase()
          ) continue;

          const coords = stationCoords[stopName];
          if (!coords) continue;
          const key = `${coords.lat.toFixed(5)},${coords.lng.toFixed(5)}`;
          if (seen.has(key)) continue;
          seen.add(key);

          markers.push({
            name: stopName,
            lat: coords.lat,
            lon: coords.lng,
            color: YELLOW,
            radius: DEFAULT_MARKER_RADIUS,
          });
        }
      }
    }

    // Center the map on the average location of all markers, or default to Times Square
    const centerLat =
      markers.length > 0
        ? markers.reduce((s, p) => s + p.lat, 0) / markers.length
        : TIMES_SQUARE_COORDS.lat;
    const centerLon =
      markers.length > 0
        ? markers.reduce((s, p) => s + p.lon, 0) / markers.length
        : TIMES_SQUARE_COORDS.lng;

    return {
      markers,
      viewState: { latitude: centerLat, longitude: centerLon, zoom: 12, pitch: 0, bearing: 0 },
    };
  }, [originName, destinationName, stations, bestRoute, stationCoords]);

  // DeckGL layer for rendering station markers
  const layers = [
    new ScatterplotLayer<MarkerPoint>({
      id: "markers",
      data: markers,
      getPosition: (d) => [d.lon, d.lat],
      getFillColor: (d) => d.color,
      getRadius: (d) => d.radius,
      pickable: true,
    }),
  ];

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <DeckGL
        initialViewState={viewState}
        controller={true}
        layers={layers}
        getTooltip={({ object }) =>
          object ? { html: `<b>${(object as MarkerPoint).name}</b>` } : null
        }
        style={{ position: "absolute", inset: "0" }}
      >
        <Map mapStyle={MAP_STYLE} />
      </DeckGL>

      <div
        className="map-legend"
        style={{ position: "absolute", bottom: 12, left: 0, right: 0 }}
      >
        <span>
          <span className="legend-dot" style={{ background: "#00ff88" }} />
          Starting Station
        </span>
        <span>
          <span className="legend-dot" style={{ background: "#ff4444" }} />
          Final Station
        </span>
        <span>
          <span className="legend-dot" style={{ background: "#facc15" }} />
          Intermediate Station
        </span>
      </div>
    </div>
  );
}
