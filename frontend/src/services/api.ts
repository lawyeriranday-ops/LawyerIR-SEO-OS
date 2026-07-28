const API_BASE = "/api/v1";

export async function fetchApiStatus(): Promise<{ service: string; ready: boolean }> {
  const response = await fetch(`${API_BASE}/status`);
  if (!response.ok) {
    throw new Error("API request failed");
  }
  return response.json();
}
