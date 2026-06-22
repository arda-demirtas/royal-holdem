"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Coins, LogOut, Trophy, Percent, Swords, Users, RefreshCw, ShoppingCart, ShieldCheck, X, AlertTriangle } from "lucide-react";
import Image from "next/image";
import Avatar from "../components/Avatar";
import { getBackendUrl, getWsUrl, getLeagueInfo } from "../utils";

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
}

interface PaymentDetails {
  payment_id: string;
  chips: number;
  amount_crypto: number;
  currency: string;
  address: string;
  qr_url: string;
}

export default function Dashboard() {
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [claiming, setClaiming] = useState(false);

  // Matchmaking Lobby States
  const [inQueue, setInQueue] = useState(false);
  const [playersInQueue, setPlayersInQueue] = useState<{username: string, avatar_id: number, chips: number}[]>([]);
  const lobbyWs = useRef<WebSocket | null>(null);

  // Crypto Payment States
  const [showBuyModal, setShowBuyModal] = useState(false);
  const [selectedChips, setSelectedChips] = useState<number>(10000); // 10000, 50000, 100000
  const [selectedCrypto, setSelectedCrypto] = useState<string>("USDT"); // 'USDT' or 'SOL'
  const [paymentDetails, setPaymentDetails] = useState<PaymentDetails | null>(null);
  const [creatingPayment, setCreatingPayment] = useState(false);
  const [verifyingPayment, setVerifyingPayment] = useState(false);
  const [paymentSuccess, setPaymentSuccess] = useState(false);
  const [paymentError, setPaymentError] = useState("");
  const [txHash, setTxHash] = useState("");
  const [showAvatarModal, setShowAvatarModal] = useState(false);

  const fetchProfile = async () => {
    const token = localStorage.getItem("poker_token");
    if (!token) {
      router.push("/");
      return;
    }

    try {
      const backendUrl = getBackendUrl();
      const response = await fetch(`${backendUrl}/api/profile?token=${token}`);
      if (!response.ok) {
        throw new Error("Failed to load profile. Please log in again.");
      }
      const data = await response.json();
      setProfile(data);
    } catch (err: any) {
      setError(err.message);
      localStorage.removeItem("poker_token");
      router.push("/");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
    return () => {
      // Close lobby WS if leaving dashboard
      if (lobbyWs.current) {
        lobbyWs.current.close();
      }
    };
  }, [router]);

  const handleLogout = () => {
    if (lobbyWs.current) {
      lobbyWs.current.close();
    }
    localStorage.removeItem("poker_token");
    router.push("/");
  };

  const handleClaimFreeChips = async () => {
    const token = localStorage.getItem("poker_token");
    if (!token) return;

    setError("");
    setClaiming(true);
    try {
      const backendUrl = getBackendUrl();
      const response = await fetch(`${backendUrl}/api/claim-free-chips?token=${token}`, {
        method: "POST",
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Claim failed");
      }
      setProfile(prev => prev ? { ...prev, chips: data.chips } : null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setClaiming(false);
    }
  };

  const handleJoinLobby = () => {
    const token = localStorage.getItem("poker_token");
    if (!token) return;

    setError("");
    setInQueue(true);
    setPlayersInQueue([]);

    // Open WebSocket to lobby matchmaking
    const wsUrl = getWsUrl();
    const ws = new WebSocket(`${wsUrl}/ws/lobby?token=${token}`);
    lobbyWs.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "lobby_status") {
        setPlayersInQueue(data.players || []);
      } else if (data.type === "match_found") {
        ws.close();
        router.push(`/play/${data.tournament_id}`);
      } else if (data.type === "error") {
        setError(data.message);
        setInQueue(false);
        ws.close();
      }
    };

    ws.onclose = () => {
      setInQueue(false);
    };

    ws.onerror = () => {
      setError("Matchmaking server connection error.");
      setInQueue(false);
    };
  };

  const handleLeaveLobby = () => {
    if (lobbyWs.current) {
      lobbyWs.current.close();
    }
    setInQueue(false);
  };

  // Crypto Payment Handlers
  const handleInitiatePayment = async () => {
    const token = localStorage.getItem("poker_token");
    if (!token) return;

    setCreatingPayment(true);
    setPaymentError("");
    try {
      const backendUrl = getBackendUrl();
      const response = await fetch(`${backendUrl}/api/crypto/create-payment?token=${token}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          chips: selectedChips,
          currency: selectedCrypto
        })
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Failed to initialize payment");
      }
      setPaymentDetails(data);
    } catch (err: any) {
      setPaymentError(err.message);
    } finally {
      setCreatingPayment(false);
    }
  };

  const handleVerifyPayment = async () => {
    if (!paymentDetails) return;
    const token = localStorage.getItem("poker_token");
    if (!token) return;

    const trimmedHash = txHash.trim();
    if (!trimmedHash) {
      setPaymentError("Please enter your transaction signature / ID / hash.");
      return;
    }

    setVerifyingPayment(true);
    setPaymentError("");

    try {
      const backendUrl = getBackendUrl();
      const response = await fetch(`${backendUrl}/api/crypto/verify-payment?token=${token}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          payment_id: paymentDetails.payment_id,
          tx_signature: trimmedHash
        })
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Payment verification failed");
      }
      setProfile(prev => prev ? { ...prev, chips: data.chips } : null);
      setPaymentSuccess(true);
    } catch (err: any) {
      setPaymentError(err.message || "We couldn't detect your payment. Please try verifying again.");
    } finally {
      setVerifyingPayment(false);
    }
  };

  const closeBuyModal = () => {
    setShowBuyModal(false);
    setPaymentDetails(null);
    setPaymentSuccess(false);
    setPaymentError("");
    setTxHash("");
    setSelectedChips(10000);
    setSelectedCrypto("USDT");
  };

  const handleSelectAvatar = async (id: number) => {
    const token = localStorage.getItem("poker_token");
    if (!token) return;
    try {
      const backendUrl = getBackendUrl();
      const response = await fetch(`${backendUrl}/api/profile/update-avatar?token=${token}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ avatar_id: id }),
      });
      if (response.ok) {
        setProfile(prev => prev ? { ...prev, avatar_id: id } : null);
        setShowAvatarModal(false);
      }
    } catch (err) {
      console.error("Failed to update avatar:", err);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-[#121214]">
        <RefreshCw className="w-8 h-8 animate-spin text-yellow-500 mb-2" />
        <span className="text-gray-400 text-sm">Loading lobby arena...</span>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-[#121214] pb-12 relative">
      {/* Decorative backdrop */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] rounded-full bg-[#0a4721]/10 blur-[150px] pointer-events-none -z-10" />

      {/* Header */}
      <header className="border-b border-white/5 bg-[#121214]/60 backdrop-blur-md sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Image
              src="/logo.png"
              alt="Royal Hold'em Logo"
              width={32}
              height={32}
              className="object-contain filter drop-shadow-[0_0_6px_rgba(250,204,21,0.2)] hover:scale-105 transition-transform duration-200"
            />
            <span className="font-black text-lg tracking-[0.12em] uppercase text-transparent bg-clip-text bg-gradient-to-r from-amber-200 via-yellow-400 to-amber-200 drop-shadow-[0_1px_2px_rgba(0,0,0,0.5)]">
              ROYAL HOLD'EM
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-yellow-500/10 border border-yellow-500/20 text-yellow-500 font-semibold text-sm">
              <Coins className="w-4 h-4" />
              <span>{profile?.chips.toLocaleString()} CHIPS</span>
            </div>

            <button
              onClick={() => setShowBuyModal(true)}
              className="gold-btn py-1.5 px-3 text-xs flex items-center gap-1 font-bold shadow-md"
            >
              <ShoppingCart className="w-3.5 h-3.5" />
              <span>BUY CHIPS</span>
            </button>

            {profile && (
              <button
                onClick={() => setShowAvatarModal(true)}
                className={`relative rounded-full p-0.5 group shrink-0 cursor-pointer transition ${getLeagueInfo(profile.chips).frameClass}`}
                title="Change Profile Avatar"
              >
                <Avatar avatarId={profile.avatar_id} className="w-8 h-8 rounded-full group-hover:scale-105 transition-transform duration-200" />
              </button>
            )}

            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 text-gray-400 hover:text-white transition text-sm font-medium"
            >
              <LogOut className="w-4 h-4" />
              <span>Log out</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 mt-8">
        {error && (
          <div className="p-4 mb-6 text-sm text-red-200 bg-red-500/15 border border-red-500/30 rounded-lg">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Left Column: Matchmaking Area */}
          <div className="md:col-span-2 space-y-6">
            <div className="glass-panel p-8 border border-white/10 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-8 opacity-[0.03] pointer-events-none">
                <Swords className="w-40 h-40" />
              </div>

              <h2 className="text-xl font-bold text-white mb-2">CHAMPIONSHIP ARENA</h2>
              <p className="text-sm text-gray-400 mb-6">
                Test your skills in standard 4-player Sit & Go tournaments. Buy in with 1,000 chips and compete to claim the grand 3,600 chips prize pool!
              </p>

              <div className="grid grid-cols-2 gap-4 text-sm mb-8">
                <div className="p-4 rounded-lg bg-white/5 border border-white/5">
                  <div className="text-gray-400 mb-1">Buy-In</div>
                  <div className="text-lg font-bold text-yellow-500">1,000 Chips</div>
                </div>
                <div className="p-4 rounded-lg bg-white/5 border border-white/5">
                  <div className="text-gray-400 mb-1">Total Prize Pool</div>
                  <div className="text-lg font-bold text-green-500">3,600 Chips (10% Rake)</div>
                </div>
              </div>

              <button
                onClick={handleJoinLobby}
                disabled={profile ? profile.chips < 1000 : true}
                className="w-full gold-btn py-4 text-base font-bold shadow-lg"
              >
                {profile && profile.chips < 1000 ? "INSUFFICIENT CHIPS (Need 1,000)" : "JOIN SIT & GO LOBBY"}
              </button>

              {profile && profile.chips < 1000 && (
                <div className="mt-4 text-center">
                  <button
                    onClick={handleClaimFreeChips}
                    disabled={claiming}
                    className="text-yellow-500 hover:text-yellow-400 hover:underline text-sm font-semibold transition"
                  >
                    {claiming ? "Claiming..." : "Claim 5,000 Free Chips"}
                  </button>
                </div>
              )}
            </div>

            {/* Quick explanation panel */}
            <div className="glass-panel p-6 border border-white/10">
              <h3 className="font-semibold text-white mb-2 text-sm uppercase tracking-wider">Tournament Rules</h3>
              <ul className="text-sm text-gray-400 space-y-2 list-disc pl-4">
                <li>Strictly 4 players. Play will not start until the table is full.</li>
                <li>Once started, the tournament is locked. No other players can join.</li>
                <li>Players start with 2,000 tournament chips.</li>
                <li>Blinds start at 20/40 and double every 5 hands.</li>
                <li>Winner takes the entire 3,600 chips prize pool.</li>
              </ul>
            </div>
          </div>

          {/* Right Column: User Stats */}
          <div className="space-y-6">
            <div className="glass-panel p-6 border border-white/10">
              <div className="flex flex-col items-center mb-6">
                <button
                  onClick={() => setShowAvatarModal(true)}
                  className={`relative rounded-full transition p-1 group mb-3 cursor-pointer ${profile ? getLeagueInfo(profile.chips).frameClass : ""}`}
                  title="Change Profile Avatar"
                >
                  {profile && <Avatar avatarId={profile.avatar_id} className="w-16 h-16 rounded-full group-hover:scale-105 transition-transform duration-200" />}
                  <span className="absolute bottom-0 right-0 w-5 h-5 rounded-full bg-yellow-500 border border-[#121214] text-[#121214] text-[10px] font-extrabold flex items-center justify-center shadow z-10">
                    ✎
                  </span>
                </button>
                <h3 className="text-lg font-bold text-white tracking-wide">{profile?.username}</h3>
                {profile && (
                  <span className={`text-[10px] font-extrabold uppercase tracking-wider px-2.5 py-0.5 rounded-full mt-1.5 ${getLeagueInfo(profile.chips).badgeClass}`}>
                    {getLeagueInfo(profile.chips).name}
                  </span>
                )}
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-white/5 pb-3">
                  <span className="text-sm text-gray-400">Username</span>
                  <span className="text-sm font-semibold text-white">{profile?.username}</span>
                </div>
                <div className="flex items-center justify-between border-b border-white/5 pb-3">
                  <span className="text-sm text-gray-400">Email</span>
                  <span className="text-sm font-semibold text-white">{profile?.email}</span>
                </div>
                <div className="flex items-center justify-between border-b border-white/5 pb-3">
                  <span className="text-sm text-gray-400 flex items-center gap-1">
                    <Swords className="w-3.5 h-3.5" /> Games Played
                  </span>
                  <span className="text-sm font-semibold text-white">{profile?.games_played}</span>
                </div>
                <div className="flex items-center justify-between border-b border-white/5 pb-3">
                  <span className="text-sm text-gray-400 flex items-center gap-1">
                    <Trophy className="w-3.5 h-3.5" /> Games Won
                  </span>
                  <span className="text-sm font-semibold text-green-500">{profile?.games_won}</span>
                </div>
                <div className="flex items-center justify-between border-b border-white/5 pb-3">
                  <span className="text-sm text-gray-400 flex items-center gap-1">
                    <Percent className="w-3.5 h-3.5" /> Tournament Win Rate
                  </span>
                  <span className="text-sm font-semibold text-yellow-500">{profile?.win_rate}%</span>
                </div>
              </div>
            </div>

            <div className="glass-panel p-6 border border-white/10">
              <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                <span>HAND STATISTICS</span>
              </h3>

              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-white/5 pb-3">
                  <span className="text-sm text-gray-400">Hands Played</span>
                  <span className="text-sm font-semibold text-white">{profile?.hands_played}</span>
                </div>
                <div className="flex items-center justify-between border-b border-white/5 pb-3">
                  <span className="text-sm text-gray-400">Hands Won</span>
                  <span className="text-sm font-semibold text-green-500">{profile?.hands_won}</span>
                </div>
                <div className="flex items-center justify-between border-b border-white/5 pb-3">
                  <span className="text-sm text-gray-400 flex items-center gap-1">
                    <Percent className="w-3.5 h-3.5" /> Hand Win Rate
                  </span>
                  <span className="text-sm font-semibold text-yellow-500">{profile?.hand_win_rate}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Matchmaking Queue Overlay */}
      {inQueue && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-md p-8 glass-panel border border-white/10 shadow-2xl relative">
            {/* Top golden indicator line */}
            <div className="absolute top-0 left-0 w-full h-[3px] bg-yellow-500 animate-pulse" />

            <div className="text-center mb-6">
              <Users className="w-12 h-12 text-yellow-500 mx-auto mb-4 animate-bounce" />
              <h3 className="text-lg font-bold text-white">SEARCHING FOR OPPONENTS</h3>
              <p className="text-sm text-gray-400 mt-1">Waiting for exactly 4 players to start the tourney...</p>
            </div>

            {/* Progress bar */}
            <div className="w-full bg-white/5 rounded-full h-2 mb-6 border border-white/5 overflow-hidden">
              <div 
                className="bg-yellow-500 h-full transition-all duration-300"
                style={{ width: `${(playersInQueue.length / 4) * 100}%` }}
              />
            </div>

            <div className="space-y-3 mb-8">
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex justify-between">
                <span>Joined Players</span>
                <span className="text-yellow-500 font-bold">{playersInQueue.length}/4</span>
              </div>

              <div className="space-y-2 max-h-40 overflow-y-auto">
                {playersInQueue.map((player, idx) => {
                  const league = getLeagueInfo(player.chips);
                  return (
                    <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5 text-sm text-white">
                      <div className="flex items-center gap-3">
                        <div className={`rounded-full p-0.5 ${league.frameClass}`}>
                          <Avatar avatarId={player.avatar_id} className="w-8 h-8 rounded-full" />
                        </div>
                        <div className="flex flex-col">
                          <span className="font-semibold">{player.username}</span>
                          <span className="text-[10px] text-gray-400 font-semibold">{league.name}</span>
                        </div>
                      </div>
                      <span className="text-xs text-green-400 font-bold">READY</span>
                    </div>
                  );
                })}
                {Array.from({ length: 4 - playersInQueue.length }).map((_, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 rounded-lg border border-dashed border-white/10 text-sm text-gray-500">
                    <span>Waiting for player...</span>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={handleLeaveLobby}
              className="w-full py-3 rounded-lg bg-red-500/15 border border-red-500/30 text-red-200 font-semibold hover:bg-red-500/25 transition text-sm"
            >
              CANCEL SEARCH
            </button>
          </div>
        </div>
      )}

      {/* Buy Chips Crypto Modal */}
      {showBuyModal && (
        <div className="fixed inset-0 bg-black/85 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-lg p-8 glass-panel border border-white/10 shadow-2xl relative">
            <button
              onClick={closeBuyModal}
              className="absolute top-4 right-4 text-gray-400 hover:text-white transition"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Title */}
            <div className="text-center mb-6">
              <ShoppingCart className="w-10 h-10 text-yellow-500 mx-auto mb-2" />
              <h3 className="text-xl font-bold text-white uppercase tracking-wider">Buy Poker Chips</h3>
              <p className="text-xs text-gray-400 mt-1">Get chips instantly using decentralized cryptocurrency.</p>
            </div>

            {paymentError && (
              <div className="flex items-center gap-2 p-3 mb-4 text-sm text-red-200 bg-red-500/10 border border-red-500/30 rounded-lg">
                <AlertTriangle className="w-4 h-4 shrink-0 text-red-400" />
                <span>{paymentError}</span>
              </div>
            )}

            {/* Payment States flow */}
            {!paymentDetails ? (
              // Step 1: Select Package & Currency
              <div className="space-y-6">
                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                    1. Select Chips Package
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { chips: 10000, price: 10, label: "10k Chips" },
                      { chips: 50000, price: 50, label: "50k Chips" },
                      { chips: 100000, price: 100, label: "100k Chips" }
                    ].map(pkg => (
                      <button
                        key={pkg.chips}
                        onClick={() => setSelectedChips(pkg.chips)}
                        className={`p-4 rounded-xl border text-center transition flex flex-col items-center ${
                          selectedChips === pkg.chips
                            ? "border-yellow-500 bg-yellow-500/10 text-yellow-500"
                            : "border-white/5 bg-white/5 text-gray-300 hover:border-white/10"
                        }`}
                      >
                        <Coins className="w-6 h-6 mb-1 text-yellow-500" />
                        <span className="font-bold text-sm">{pkg.label}</span>
                        <span className="text-[10px] text-gray-400 mt-1">${pkg.price} USD</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                    2. Choose Cryptocurrency
                  </label>
                  <div className="grid grid-cols-2 gap-4">
                    {[
                      { id: "USDT", name: "Tether (USDT)", desc: "TRON network (TRC-20)", color: "text-emerald-400" },
                      { id: "SOL", name: "Solana (SOL)", desc: "Solana network", color: "text-indigo-400" }
                    ].map(crypto => (
                      <button
                        key={crypto.id}
                        onClick={() => setSelectedCrypto(crypto.id)}
                        className={`p-4 rounded-xl border text-left transition ${
                          selectedCrypto === crypto.id
                            ? "border-yellow-500 bg-yellow-500/10"
                            : "border-white/5 bg-white/5 hover:border-white/10"
                        }`}
                      >
                        <span className={`font-bold block ${crypto.color}`}>{crypto.name}</span>
                        <span className="text-[10px] text-gray-400 mt-0.5">{crypto.desc}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  onClick={handleInitiatePayment}
                  disabled={creatingPayment}
                  className="w-full gold-btn py-3.5 text-sm font-bold shadow-lg"
                >
                  {creatingPayment ? "Creating payment details..." : `GENERATE PAYMENT OF $${(selectedChips / 1000).toFixed(0)}`}
                </button>
              </div>
            ) : paymentSuccess ? (
              // Step 3: Success Screen
              <div className="text-center py-6 space-y-6">
                <div className="w-16 h-16 rounded-full bg-green-500/10 border border-green-500/30 flex items-center justify-center mx-auto text-green-500">
                  <ShieldCheck className="w-10 h-10" />
                </div>
                <div>
                  <h4 className="text-lg font-bold text-white">Payment Confirmed!</h4>
                  <p className="text-xs text-gray-400 mt-1">
                    Your {selectedChips.toLocaleString()} chips have been credited to your account.
                  </p>
                </div>
                <button onClick={closeBuyModal} className="gold-btn w-full py-3">
                  AWESOME
                </button>
              </div>
            ) : (
              // Step 2: Payment Details with QR Code
              <div className="space-y-6">
                <div className="flex flex-col md:flex-row items-center gap-6 p-4 rounded-xl bg-white/5 border border-white/5">
                  {/* QR Code Container */}
                  <div className="w-[160px] h-[160px] bg-white rounded-lg flex items-center justify-center p-2 shrink-0">
                    {/* Embedded QR code image */}
                    <img 
                      src={paymentDetails.qr_url} 
                      alt="Payment QR Code" 
                      className="w-full h-full object-contain"
                    />
                  </div>

                  {/* Payment Info details */}
                  <div className="flex-1 space-y-3 min-w-0 text-left">
                    <div>
                      <span className="text-[10px] text-gray-400 block uppercase tracking-widest font-semibold">Send Exactly</span>
                      <span className="text-xl font-black text-yellow-500">
                        {paymentDetails.amount_crypto} {paymentDetails.currency}
                      </span>
                      <span className="text-xs text-gray-500 ml-1.5">~ ${(paymentDetails.chips / 1000).toFixed(0)} USD</span>
                    </div>

                    <div className="min-w-0">
                      <span className="text-[10px] text-gray-400 block uppercase tracking-widest font-semibold">Deposit Address</span>
                      <span className="text-xs font-mono text-gray-300 break-all select-all select-text block bg-black/40 p-2 rounded border border-white/5 mt-1">
                        {paymentDetails.address}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider text-left">
                    3. Enter Transaction Hash / Signature / TxID
                  </label>
                  <input
                    type="text"
                    value={txHash}
                    onChange={(e) => setTxHash(e.target.value)}
                    placeholder={
                      selectedCrypto === "SOL"
                        ? "Solana transaction signature (e.g. 5Kz...)"
                        : "TRON transaction hash/ID (e.g. f83...)"
                    }
                    className="w-full glass-input text-sm text-white"
                  />
                  <p className="text-[10px] text-gray-500 text-left leading-normal">
                    You can find your transaction hash/signature inside your crypto wallet app under transaction history after sending the payment.
                  </p>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => setPaymentDetails(null)}
                    disabled={verifyingPayment}
                    className="flex-1 py-3 bg-white/5 border border-white/5 rounded-lg text-sm text-gray-400 font-semibold hover:bg-white/10 transition"
                  >
                    GO BACK
                  </button>
                  <button
                    onClick={handleVerifyPayment}
                    disabled={verifyingPayment}
                    className="flex-1 gold-btn py-3 text-sm font-bold flex items-center justify-center gap-1.5"
                  >
                    {verifyingPayment ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Verifying...</span>
                      </>
                    ) : (
                      <span>VERIFY DEPOSIT</span>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Edit Avatar Modal */}
      {showAvatarModal && (
        <div className="fixed inset-0 bg-black/85 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-md p-8 glass-panel border border-white/10 shadow-2xl relative">
            <button
              onClick={() => setShowAvatarModal(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-white transition cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="text-center mb-6">
              <Trophy className="w-10 h-10 text-yellow-500 mx-auto mb-2" />
              <h3 className="text-xl font-bold text-white uppercase tracking-wider">Choose Profile Avatar</h3>
              <p className="text-xs text-gray-400 mt-1">Select one of our luxury poker-themed avatars.</p>
            </div>

            <div className="grid grid-cols-4 gap-4 mb-6">
              {[1, 2, 3, 4, 5, 6, 7, 8].map((id) => (
                <button
                  key={id}
                  onClick={() => handleSelectAvatar(id)}
                  className={`p-1.5 rounded-xl border transition hover:scale-105 duration-200 cursor-pointer ${
                    profile?.avatar_id === id
                      ? "border-yellow-500 bg-yellow-500/10 shadow-[0_0_10px_rgba(212,175,55,0.2)]"
                      : "border-white/5 bg-white/5 hover:border-white/10"
                  }`}
                >
                  <Avatar avatarId={id} className="w-full h-full rounded-full" />
                </button>
              ))}
            </div>

            <button
              onClick={() => setShowAvatarModal(false)}
              className="w-full py-3 bg-white/5 border border-white/5 rounded-lg text-sm text-gray-400 font-semibold hover:bg-white/10 transition cursor-pointer"
            >
              CANCEL
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
