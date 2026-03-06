import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchStations, fetchRoutes, fetchStationCoords } from "./api/client";
import { Header } from "./components/Header";
import { SearchInputs } from "./components/SearchInputs";
import { SearchResults } from "./components/SearchResults";
import { MapView } from "./components/MapView";
import type { Route } from "./types";

function App() {
  const { data: stations = {} } = useQuery({
    queryKey: ["stations"],
    queryFn: fetchStations,
    staleTime: Infinity,
  });

  const stationNames = useMemo(() =>
    Object.keys(stations).sort(), [stations]);

  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [searched, setSearched] = useState(false);

  // Derive effective values: fall back to first/second station before user picks
  const effectiveOrigin = origin || stationNames[0] || "";
  const effectiveDestination =
    destination || stationNames[Math.min(1, stationNames.length - 1)] || "";

  const effectiveOriginId = stations[effectiveOrigin]?.id ?? "";
  const effectiveDestinationId = stations[effectiveDestination]?.id ?? "";

  const {
    data: routesData,
    error,
    isFetching,
    refetch,
  } = useQuery({
    queryKey: ["routes", effectiveOriginId, effectiveDestinationId],
    queryFn: () => fetchRoutes(effectiveOriginId, effectiveDestinationId),
    enabled: false,
    retry: false,
  });

  function handleSearch() {
    if (!effectiveOriginId || !effectiveDestinationId || effectiveOriginId === effectiveDestinationId) return;
    setSearched(true);
    refetch();
  }

  const bestRoute: Route | null = useMemo(() => {
    if (!routesData) return null;
    return routesData.routes.find((r) => r.is_recommended) ?? routesData.routes[0] ?? null;
  }, [routesData]);

  // Fetch coordinates for intermediate stop names that appear in the best route
  const stopNames = useMemo(() => {
    if (!bestRoute) return [];
    const names = new Set<string>();
    for (const step of bestRoute.steps) {
      if (step.type !== "transit") continue;
      if (step.departure) names.add(step.departure);
      if (step.arrival) names.add(step.arrival);
    }
    return Array.from(names);
  }, [bestRoute]);

  const coordQueries = useQuery({
    queryKey: ["stationCoords", stopNames],
    queryFn: async () => {
      const entries = await Promise.all(
        stopNames.map(async (name) => {
          const result = await fetchStationCoords(name);
          return result ? ([name, result] as const) : null;
        })
      );
      return Object.fromEntries(entries.filter(Boolean) as [string, { lat: number; lng: number; name: string }][]);
    },
    enabled: stopNames.length > 0,
    staleTime: Infinity,
  });

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <Header />
        <SearchInputs
          stationNames={stationNames}
          origin={effectiveOrigin}
          destination={effectiveDestination}
          onOriginChange={setOrigin}
          onDestinationChange={setDestination}
          onSearch={handleSearch}
          loading={isFetching}
        />
        <SearchResults
          data={routesData}
          error={error instanceof Error ? error : null}
          isLoading={isFetching}
          searched={searched}
          originName={effectiveOrigin}
          destinationName={effectiveDestination}
        />
      </aside>

      <main style={{ position: "relative", width: "100%", height: "100%" }}>
        <MapView
          originName={effectiveOrigin}
          destinationName={effectiveDestination}
          stations={stations}
          bestRoute={bestRoute}
          stationCoords={coordQueries.data ?? {}}
        />
      </main>
    </div>
  );
}

export default App;
