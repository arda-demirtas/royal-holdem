export const getBackendUrl = () => {
  if (typeof window === "undefined") return "";
  const host = window.location.hostname;
  if (host === "localhost" || host === "127.0.0.1") {
    return "http://127.0.0.1:8000";
  }
  return `${window.location.protocol}//${window.location.host}`;
};

export const getWsUrl = () => {
  if (typeof window === "undefined") return "";
  const host = window.location.hostname;
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  if (host === "localhost" || host === "127.0.0.1") {
    return `ws://127.0.0.1:8000`;
  }
  return `${protocol}//${window.location.host}`;
};
