import type { Station, RoutesResponse } from "../types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

export async function fetchStations(): Promise<Record<string, Station>> {
  const res = await fetch(`${API_URL}/stations`);
  if (!res.ok) throw new Error("Failed to load stations");
  return res.json();
}

export async function fetchRoutes(
  originId: string,
  destId: string
): Promise<RoutesResponse> {
  const params = new URLSearchParams({ origin_id: originId, destination_id: destId });
  const res = await fetch(`${API_URL}/routes?${params}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? "Failed to fetch routes");
  }
  return res.json();
}

export async function fetchStationCoords(
  name: string
): Promise<{ lat: number; lng: number; name: string } | null> {
  const params = new URLSearchParams({ name });
  const res = await fetch(`${API_URL}/station-coords?${params}`);
  if (!res.ok) return null;
  return res.json();
}
