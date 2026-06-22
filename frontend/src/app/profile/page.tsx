"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Trophy, Percent, Swords, ShieldCheck, Mail, User, Coins, RefreshCw, LogOut, Edit2, ShoppingCart } from "lucide-react";
import Image from "next/image";
import Avatar from "../components/Avatar";
import { getBackendUrl, getLeagueInfo } from "../utils";
import { translations, Language } from "../translations";

interface UserProfile {
  id: number;
  username: string;
  email: string;
  chips: number;
  avatar_id: number;
  games_played: number;
  games_won: number;
  hands_played: number;
  hands_won: number;
  win_rate: number;
  hand_win_rate: number;
  lp: number;
  league_tier: number;
  league_division: number;
}

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lang, setLang] = useState<Language>("en");
  const [showAvatarGrid, setShowAvatarGrid] = useState(false);
  const [updatingAvatar, setUpdatingAvatar] = useState(false);

  useEffect(() => {
    const savedLang = localStorage.getItem("poker_lang") as Language;
    if (savedLang && ["en", "tr", "de", "ru", "zh"].includes(savedLang)) {
      setLang(savedLang);
    }

    const token = localStorage.getItem("poker_token");
    if (!token) {
      router.push("/");
      return;
    }

    const fetchProfile = async () => {
      try {
        const backendUrl = getBackendUrl();
        const response = await fetch(`${backendUrl}/api/profile?token=${token}`);
        if (!response.ok) {
          throw new Error("Failed to load profile.");
        }
        const data = await response.json();
        setProfile(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [router]);

  const handleLanguageChange = (newLang: Language) => {
    setLang(newLang);
    localStorage.setItem("poker_lang", newLang);
  };

  const handleSelectAvatar = async (avatarId: number) => {
    const token = localStorage.getItem("poker_token");
    if (!token) return;
    setUpdatingAvatar(true);
    try {
      const backendUrl = getBackendUrl();
      const response = await fetch(`${backendUrl}/api/profile/update-avatar?token=${token}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ avatar_id: avatarId }),
      });
      if (response.ok) {
        setProfile(prev => prev ? { ...prev, avatar_id: avatarId } : null);
        setShowAvatarGrid(false);
      }
    } catch (err) {
      console.error("Failed to update avatar:", err);
    } finally {
      setUpdatingAvatar(false);
    }
  };

  const t = translations[lang];

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-[#121214]">
        <RefreshCw className="w-8 h-8 animate-spin text-yellow-500 mb-2" />
        <span className="text-gray-400 text-sm">{t.loading}</span>
      </div>
    );
  }

  const league = profile ? getLeagueInfo(profile.league_tier, profile.league_division) : null;

  return (
    <div className="min-h-screen bg-[#121214] text-white flex flex-col relative overflow-x-hidden">
      {/* Background radial glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[500px] rounded-full bg-[#0a4721]/10 blur-[150px] pointer-events-none -z-10" />

      {/* Header */}
      <header className="border-b border-white/5 bg-[#121214]/60 backdrop-blur-md px-6 py-4 flex items-center justify-between shrink-0">
        <button
          onClick={() => {
            const referrer = document.referrer;
            if (referrer.includes("/play/")) {
              window.history.back();
            } else {
              router.push("/dashboard");
            }
          }}
          className="text-gray-400 hover:text-white transition flex items-center gap-1 text-sm font-semibold"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>{t.go_back}</span>
        </button>

        <div className="flex items-center gap-2">
          <Image
            src="/logo.png"
            alt="Royal Hold'em Logo"
            width={24}
            height={24}
            className="object-contain"
          />
          <span className="font-black text-sm tracking-widest text-yellow-500 uppercase">ROYAL PROFILE</span>
        </div>
        <div className="w-16"></div> {/* Spacer for symmetry */}
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-lg mx-auto w-full px-4 py-8 space-y-6">
        {error ? (
          <div className="p-4 text-sm text-red-200 bg-red-500/15 border border-red-500/30 rounded-lg">
            {error}
          </div>
        ) : profile && league ? (
          <>
            {/* Profile Overview Card */}
            <div className="glass-panel p-6 border border-white/10 flex flex-col items-center text-center relative">
              <div className="relative group">
                <div className={`relative rounded-full p-1 ${league.frameClass}`}>
                  <Avatar avatarId={profile.avatar_id} className="w-20 h-20 rounded-full" />
                </div>
                <button
                  onClick={() => setShowAvatarGrid(prev => !prev)}
                  className="absolute bottom-0 right-0 w-6 h-6 rounded-full bg-yellow-500 border border-[#121214] text-[#121214] text-xs font-bold flex items-center justify-center shadow hover:scale-110 active:scale-95 transition cursor-pointer"
                  title="Change Avatar"
                >
                  <Edit2 className="w-3 h-3" />
                </button>
              </div>
              <h2 className="text-xl font-bold text-white tracking-wide mt-4">{profile.username}</h2>
              <span className={`text-[10px] font-extrabold uppercase tracking-wider px-3 py-1 rounded-full mt-2 ${league.badgeClass}`}>
                {league.divisionName}
              </span>
              <p className="text-xs text-gray-500 mt-2 font-mono">{profile.email}</p>
            </div>

            {/* Avatar selection grid */}
            {showAvatarGrid && (
              <div className="glass-panel p-5 border border-white/10 space-y-4 animate-in fade-in slide-in-from-top-3 duration-200">
                <div className="flex items-center justify-between border-b border-white/5 pb-2">
                  <h4 className="text-xs font-black uppercase tracking-wider text-yellow-500">
                    {lang === "tr" ? "Profil Resmi Seçin" : "Select Profile Avatar"}
                  </h4>
                  <button 
                    onClick={() => setShowAvatarGrid(false)}
                    className="text-gray-400 hover:text-white text-xs font-bold transition"
                  >
                    {t.cancel}
                  </button>
                </div>
                <div className="grid grid-cols-4 gap-3 py-1">
                  {[1, 2, 3, 4, 5, 6, 7, 8].map(id => (
                    <button
                      key={id}
                      onClick={() => handleSelectAvatar(id)}
                      disabled={updatingAvatar}
                      className={`relative rounded-full p-0.5 border-2 transition hover:scale-105 active:scale-95 cursor-pointer ${
                        profile.avatar_id === id ? "border-yellow-500 scale-105" : "border-transparent hover:border-white/20"
                      }`}
                    >
                      <Avatar avatarId={id} className="w-12 h-12 rounded-full" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Balances Card */}
            <div className="glass-panel p-5 border border-white/10 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-white/5 border border-white/5 text-center">
                  <Coins className="w-5 h-5 text-yellow-500 mx-auto mb-1" />
                  <span className="text-[10px] text-gray-400 block uppercase tracking-wider mb-1">Chips Balance</span>
                  <span className="font-black text-sm text-yellow-500">{profile.chips.toLocaleString()} {t.chps_display}</span>
                </div>
                <div className="p-4 rounded-xl bg-white/5 border border-white/5 text-center">
                  <Trophy className="w-5 h-5 text-yellow-400 mx-auto mb-1" />
                  <span className="text-[10px] text-gray-400 block uppercase tracking-wider mb-1">League Points</span>
                  <span className="font-black text-sm text-yellow-400">{profile.lp} LP</span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 pt-1">
                <button
                  onClick={() => router.push("/dashboard?buy=true")}
                  className="gold-btn py-2.5 px-4 text-xs font-bold flex items-center justify-center gap-1.5 shadow"
                >
                  <ShoppingCart className="w-3.5 h-3.5" />
                  <span>{t.buy_chips}</span>
                </button>
                <button
                  onClick={() => router.push("/dashboard?withdraw=true")}
                  className="py-2.5 px-4 text-xs font-bold rounded-lg bg-white/5 border border-white/10 text-gray-300 hover:bg-white/10 hover:text-white transition flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <Coins className="w-3.5 h-3.5 text-yellow-500" />
                  <span>{t.withdraw_chips}</span>
                </button>
              </div>
            </div>

            {/* Settings Selector */}
            <div className="glass-panel p-5 border border-white/10 flex items-center justify-between">
              <span className="text-sm text-gray-400 font-semibold">{t.profile_lang}</span>
              <select
                value={lang}
                onChange={(e) => handleLanguageChange(e.target.value as Language)}
                className="bg-black/60 border border-white/10 text-gray-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-yellow-500/50 cursor-pointer font-semibold"
              >
                <option value="en">English</option>
                <option value="tr">Türkçe</option>
                <option value="de">Deutsch</option>
                <option value="ru">Русский</option>
                <option value="zh">中文</option>
              </select>
            </div>

            {/* Statistics */}
            <div className="glass-panel p-5 border border-white/10 space-y-4">
              <h3 className="text-xs font-black uppercase tracking-wider text-gray-400 border-b border-white/5 pb-2">
                Tournament Statistics
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400 flex items-center gap-2">
                    <Swords className="w-4 h-4" /> Games Played
                  </span>
                  <span className="font-bold text-white">{profile.games_played}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400 flex items-center gap-2">
                    <Trophy className="w-4 h-4 text-green-500" /> Games Won
                  </span>
                  <span className="font-bold text-green-400">{profile.games_won}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400 flex items-center gap-2">
                    <Percent className="w-4 h-4 text-yellow-500" /> Tournament Win Rate
                  </span>
                  <span className="font-bold text-yellow-400">{profile.win_rate}%</span>
                </div>
              </div>
            </div>

            {/* Hand Stats */}
            <div className="glass-panel p-5 border border-white/10 space-y-4">
              <h3 className="text-xs font-black uppercase tracking-wider text-gray-400 border-b border-white/5 pb-2">
                Hand Statistics
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400 flex items-center gap-2">
                    <Swords className="w-4 h-4" /> Hands Played
                  </span>
                  <span className="font-bold text-white">{profile.hands_played}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400 flex items-center gap-2">
                    <Trophy className="w-4 h-4 text-green-500" /> Hands Won
                  </span>
                  <span className="font-bold text-green-400">{profile.hands_won}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400 flex items-center gap-2">
                    <Percent className="w-4 h-4 text-yellow-500" /> Hand Win Rate
                  </span>
                  <span className="font-bold text-yellow-400">{profile.hand_win_rate}%</span>
                </div>
              </div>
            </div>

            {/* Log Out Button */}
            <button
              onClick={() => {
                localStorage.removeItem("poker_token");
                router.push("/");
              }}
              className="w-full py-3 bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20 rounded-xl transition text-sm font-bold flex items-center justify-center gap-2 cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
              <span>{t.log_out}</span>
            </button>
          </>
        ) : null}
      </main>
    </div>
  );
}
