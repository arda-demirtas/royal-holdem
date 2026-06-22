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

export interface LeagueInfo {
  name: string;
  nameTr: string;
  tier: number;
  color: string;
  frameClass: string;
  badgeClass: string;
}

export const getLeagueInfo = (chips: number): LeagueInfo => {
  if (chips < 50000) {
    return {
      name: "Jacks Club",
      nameTr: "Vale Kulübü",
      tier: 1,
      color: "bronze",
      frameClass: "ring-2 ring-amber-800 shadow-[0_0_8px_rgba(146,64,14,0.3)]",
      badgeClass: "bg-amber-800/20 text-amber-300 border border-amber-800/40",
    };
  } else if (chips < 150000) {
    return {
      name: "Queens Alliance",
      nameTr: "Kız Birliği",
      tier: 2,
      color: "silver",
      frameClass: "ring-2 ring-slate-400 shadow-[0_0_8px_rgba(203,213,225,0.4)]",
      badgeClass: "bg-slate-400/20 text-slate-300 border border-slate-400/40",
    };
  } else if (chips < 500000) {
    return {
      name: "Kings Fellowship",
      nameTr: "Kral Meclisi",
      tier: 3,
      color: "gold",
      frameClass: "ring-2 ring-yellow-500 shadow-[0_0_12px_rgba(234,179,8,0.5)]",
      badgeClass: "bg-yellow-500/20 text-yellow-300 border border-yellow-500/40",
    };
  } else if (chips < 2000000) {
    return {
      name: "Aces Syndicate",
      nameTr: "Aslar Birliği",
      tier: 4,
      color: "platinum",
      frameClass: "ring-2 ring-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.6)] animate-pulse",
      badgeClass: "bg-cyan-500/20 text-cyan-300 border border-cyan-400/40",
    };
  } else {
    return {
      name: "Royal Sovereign",
      nameTr: "Kraliyet Hanedanı",
      tier: 5,
      color: "royal",
      frameClass: "ring-2 ring-purple-500 shadow-[0_0_20px_rgba(168,85,247,0.8)] animate-[active-player-pulse_1.5s_infinite]",
      badgeClass: "bg-purple-500/20 text-purple-300 border border-purple-400/40",
    };
  }
};

