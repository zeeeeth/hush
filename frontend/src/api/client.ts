import type { Station, RoutesResponse } from "../types";
import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

export async function fetchStations(): Promise<Record<string, Station>> {
  const res = await axios.get(`${API_URL}/stations`);
  return res.data;
}

export async function fetchRoutes(
  originId: string,
  destId: string
): Promise<RoutesResponse> {
  const params = new URLSearchParams({ origin_id: originId, destination_id: destId });
  const res = await axios.get(`${API_URL}/routes`, { params });
  if (!res.data) {
    const body = await res.data.catch(() => ({}));
    throw new Error(body.detail ?? "Failed to fetch routes");
  }
  return res.data;
}

export async function fetchStationCoords(
  name: string
): Promise<{ lat: number; lng: number; name: string } | null> {
  const params = new URLSearchParams({ name });
  const res = await axios.get(`${API_URL}/station-coords`, { params });
  if (!res.data) return null;
  return res.data;
}
