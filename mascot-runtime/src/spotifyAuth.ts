const clientId = import.meta.env.VITE_SPOTIFY_CLIENT_ID as string | undefined;
const redirectUri = (import.meta.env.VITE_SPOTIFY_REDIRECT_URI as string | undefined) || `${window.location.origin}/callback`;
const verifierKey = "nova-spotify-code-verifier";

function randomString(length = 64) { const bytes = crypto.getRandomValues(new Uint8Array(length)); return Array.from(bytes, (byte) => (byte % 36).toString(36)).join(""); }
async function challenge(verifier: string) { const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier)); return btoa(String.fromCharCode(...new Uint8Array(digest))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""); }

export async function connectSpotify() {
  if (!clientId) throw new Error("Spotify Client ID não configurado");
  const verifier = randomString(); localStorage.setItem(verifierKey, verifier);
  const params = new URLSearchParams({ client_id: clientId, response_type: "code", redirect_uri: redirectUri, code_challenge_method: "S256", code_challenge: await challenge(verifier), scope: "user-read-currently-playing user-read-playback-state" });
  window.location.assign(`https://accounts.spotify.com/authorize?${params}`);
}

export async function exchangeSpotifyCode(code: string) {
  if (!clientId) throw new Error("Spotify Client ID não configurado");
  const verifier = localStorage.getItem(verifierKey); if (!verifier) throw new Error("PKCE verifier não encontrado");
  const response = await fetch("https://accounts.spotify.com/api/token", { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: new URLSearchParams({ client_id: clientId, grant_type: "authorization_code", code, redirect_uri: redirectUri, code_verifier: verifier }) });
  if (!response.ok) {
    let detail = "resposta inválida do Spotify";
    try { const body = await response.json() as { error?: string; error_description?: string }; detail = body.error_description || body.error || detail; } catch { /* resposta sem JSON */ }
    throw new Error(detail);
  }
  localStorage.removeItem(verifierKey); return response.json() as Promise<{ access_token: string; expires_in: number; refresh_token?: string }>;
}

export type SpotifyPlayback = {
  is_playing: boolean;
  progress_ms: number;
  item: { name: string; duration_ms: number; artists: Array<{ name: string }> } | null;
};

export type SpotifyDevice = { name: string; type: string; is_active: boolean; is_restricted?: boolean };

export function getStoredSpotifyToken() {
  return localStorage.getItem("nova-spotify-access-token");
}

export async function getSpotifyDevices(): Promise<SpotifyDevice[]> {
  const token = getStoredSpotifyToken();
  if (!token) return [];
  const response = await fetch("https://api.spotify.com/v1/me/player/devices", { headers: { Authorization: `Bearer ${token}` } });
  if (!response.ok) throw new Error(`Dispositivos Spotify: erro ${response.status}`);
  const body = await response.json() as { devices?: SpotifyDevice[] };
  return body.devices ?? [];
}

export async function getCurrentPlayback(): Promise<SpotifyPlayback | null> {
  const token = getStoredSpotifyToken();
  if (!token) return null;
  const response = await fetch("https://api.spotify.com/v1/me/player?market=BR&additional_types=track", {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (response.status === 204) return null;
  if (response.status === 401) {
    localStorage.removeItem("nova-spotify-access-token");
    throw new Error("Sessão do Spotify expirada");
  }
  if (response.status === 403) {
    const fallback = await fetch("https://api.spotify.com/v1/me/player/currently-playing?market=BR", { headers: { Authorization: `Bearer ${token}` } });
    if (fallback.status === 204) return null;
    if (fallback.ok) {
      const current = await fallback.json() as { is_playing: boolean; progress_ms: number; item: SpotifyPlayback["item"] };
      return { is_playing: current.is_playing, progress_ms: current.progress_ms, item: current.item };
    }
    throw new Error("Spotify bloqueou a consulta da reprodução nesta conta ou dispositivo");
  }
  if (!response.ok) throw new Error(`Spotify respondeu com erro ${response.status}`);
  return response.json() as Promise<SpotifyPlayback>;
}
