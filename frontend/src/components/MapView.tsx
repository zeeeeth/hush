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

const MAP_STYLE =
  "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

export function MapView({
  originName,
  destinationName,
  stations,
  bestRoute,
  stationCoords,
}: Props) {
  const { markers, intermediates, viewState } = useMemo(() => {
    const markers: MarkerPoint[] = [];
    const intermediates: MarkerPoint[] = [];

    const origin = stations[originName];
    const dest = stations[destinationName];

    if (origin?.lat && origin?.lng) {
      markers.push({
        name: originName,
        lat: origin.lat,
        lon: origin.lng,
        color: [0, 255, 136, 255],
        radius: 100,
      });
    }
    if (dest?.lat && dest?.lng) {
      markers.push({
        name: destinationName,
        lat: dest.lat,
        lon: dest.lng,
        color: [255, 68, 68, 255],
        radius: 100,
      });
    }

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

          intermediates.push({
            name: stopName,
            lat: coords.lat,
            lon: coords.lng,
            color: [250, 204, 21, 255],
            radius: 100,
          });
        }
      }
    }

    const all = [...markers, ...intermediates];
    const centerLat =
      all.length > 0
        ? all.reduce((s, p) => s + p.lat, 0) / all.length
        : 40.758;
    const centerLon =
      all.length > 0
        ? all.reduce((s, p) => s + p.lon, 0) / all.length
        : -73.9855;

    return {
      markers,
      intermediates,
      viewState: { latitude: centerLat, longitude: centerLon, zoom: 12, pitch: 0, bearing: 0 },
    };
  }, [originName, destinationName, stations, bestRoute, stationCoords]);

  const layers = [
    new ScatterplotLayer<MarkerPoint>({
      id: "intermediate-stations",
      data: intermediates,
      getPosition: (d) => [d.lon, d.lat],
      getColor: (d) => d.color,
      getRadius: (d) => d.radius,
      pickable: true,
    }),
    new ScatterplotLayer<MarkerPoint>({
      id: "main-markers",
      data: markers,
      getPosition: (d) => [d.lon, d.lat],
      getColor: (d) => d.color,
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
