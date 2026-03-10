import { useState, useMemo } from "react";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { fetchStations, fetchRoutes, fetchStationCoords } from "./api/client";
import { Header } from "./components/Header";
import { SearchInputs } from "./components/SearchInputs";
import { SearchResults } from "./components/SearchResults";
import { MapView } from "./components/MapView";
import type { Route } from "./types";

function App() {
  // Fetch stations once on load - { {stationName: { id, lat, lng } } }
  const { data: stations = {} } = useQuery({
    queryKey: ["stations"],
    queryFn: fetchStations,
    staleTime: Infinity, // never refetch unless page reloads
  });

  // Sorted array of keys from stations, used for dropdown options
  const stationNames = useMemo(() =>
    Object.keys(stations).sort(), [stations]);

  // User-selected origin/destination from dropdowns
  // Initially empty, but fallback to first/second station in list for search until user picks
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [searched, setSearched] = useState(false);

  const effectiveOrigin = origin || stationNames[0] || "";
  const effectiveDestination = destination || stationNames[1] || "";
  
  const effectiveOriginId = stations[effectiveOrigin]?.id ?? "";
  const effectiveDestinationId = stations[effectiveDestination]?.id ?? "";

  // Route fetch
  const { data: routesData, error, isFetching, refetch } = useQuery({
    queryKey: ["routes", effectiveOriginId, effectiveDestinationId],
    queryFn: () => fetchRoutes(effectiveOriginId, effectiveDestinationId),
    enabled: false, // Do not run on mount or when origin/destination changes - only when user clicks "Find Routes"
    retry: false,
    placeholderData: keepPreviousData, // Keep old results visible while user changes dropdowns
  });

  // Handler for when user clicks "Find Routes" - validate input and trigger route fetch
  function handleSearch() {
    if (!effectiveOriginId || !effectiveDestinationId || effectiveOriginId === effectiveDestinationId) return;
    setSearched(true);  // Render search results section
    refetch();          // Trigger the route fetch query -> routesData updates -> triggers re-render of SearchResults
  }

  // Update best route to pass to the map for showing intermediate stops - triggered on routesData update
  const bestRoute: Route | null = useMemo(() => {
    if (!routesData) return null;
    return routesData.routes.find((r) => r.is_recommended) ?? routesData.routes[0] ?? null;
  }, [routesData]);

  // Collect unique stop names that appear in the best route - triggered on bestRoute update
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

  // Fetch coordinates for all stops in the best route to show on the map - triggered on stopNames update
  const coordQueries = useQuery({
    queryKey: ["stationCoords", stopNames],
    queryFn: async () => {
        const entries = []
        for (const name of stopNames) {
            const result = await fetchStationCoords(name);
            if (result) {
                entries.push([name, result]);
            }
        }
        return Object.fromEntries(entries);
    },
    enabled: stopNames.length > 0,
    staleTime: Infinity,
  });

  /*┌─────────────────────┬───────────────┐
    │  <aside.sidebar>    │  <main>       │
    │  <Header />         │  <MapView />  │
    │  <SearchInputs />   │               │
    │  <SearchResults />  │               │
    └─────────────────────┴───────────────┘ */
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
