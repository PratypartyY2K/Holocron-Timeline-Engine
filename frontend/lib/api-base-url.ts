const DEFAULT_BROWSER_API_BASE_URL = "http://localhost:8000";
const DEFAULT_SERVER_API_BASE_URL = "http://backend:8000";

function resolveBrowserApiBaseUrl(configuredApiBaseUrl: string | undefined): string {
  if (!configuredApiBaseUrl) {
    return DEFAULT_BROWSER_API_BASE_URL;
  }

  try {
    const url = new URL(configuredApiBaseUrl);
    if (url.hostname === "backend") {
      url.hostname = "localhost";
    }
    return url.toString().replace(/\/$/, "");
  } catch {
    return configuredApiBaseUrl;
  }
}

export function getApiBaseUrl(): string {
  const configuredApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (typeof window === "undefined") {
    return configuredApiBaseUrl ?? DEFAULT_SERVER_API_BASE_URL;
  }
  return resolveBrowserApiBaseUrl(configuredApiBaseUrl);
}
