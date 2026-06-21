"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import { Coins, LogOut, ArrowLeft, ShieldAlert, Check, RefreshCw } from "lucide-react";
import { getBackendUrl, getWsUrl } from "../../utils";

interface CardData {
  rank: string;
  suit: string;
}

interface PlayerData {
  user_id: number;
  username: string;
  chips: number;
  cards: CardData[];
  is_folded: boolean;
  is_all_in: boolean;
  current_bet: number;
  chips_in_pot: number;
  is_connected: boolean;
  seat_index: number;
  last_action: string | null;
  hand_description: string | null;
}

interface GameState {
  tournament_id: string;
  players: PlayerData[];
  community_cards: CardData[];
  pot: number;
  betting_round: string;
  current_bet: number;
  min_raise: number;
  dealer_index: number;
  current_turn_index: number;
  small_blind: number;
  big_blind: number;
  hand_count: number;
  game_log: string[];
  winner_id: number | null;
}

export default function PlayRoom() {
  const router = useRouter();
  const params = useParams();
  const roomId = params.roomId as string;

  const [gameState, setGameState] = useState<GameState | null>(null);
  const [myUserId, setMyUserId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [wsConnected, setWsConnected] = useState(false);
  const [raiseAmount, setRaiseAmount] = useState<number>(0);
  const [showWinnerModal, setShowWinnerModal] = useState(false);
  const [winnerName, setWinnerName] = useState("");

  const ws = useRef<WebSocket | null>(null);
  const logContainerRef = useRef<HTMLDivElement>(null);

  // Load user profile to get own user_id
  useEffect(() => {
    const token = localStorage.getItem("poker_token");
    if (!token) {
      router.push("/");
      return;
    }

    // Fetch own profile
    const backendUrl = getBackendUrl();
    fetch(`${backendUrl}/api/profile?token=${token}`)
      .then(res => {
        if (!res.ok) throw new Error("Auth failed");
        return res.json();
      })
      .then(data => {
        setMyUserId(data.id);
      })
      .catch(() => {
        localStorage.removeItem("poker_token");
        router.push("/");
      });
  }, [router]);

  // Connect to Game WebSocket
  useEffect(() => {
    if (!myUserId || !roomId) return;

    const wsUrl = getWsUrl();
    const socket = new WebSocket(`${wsUrl}/ws/play/${roomId}?token=${token}`);
    ws.current = socket;

    socket.onopen = () => {
      setWsConnected(true);
      setError("");
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "game_state") {
        const state: GameState = data.state;
        setGameState(state);

        // Auto initialize raise amount to minimum raise
        const me = state.players.find(p => p.user_id === myUserId);
        if (me) {
          const defaultRaise = Math.min(state.min_raise, me.chips + me.current_bet);
          setRaiseAmount(defaultRaise);
        }

        // If game is finished
        if (state.betting_round === "finished" && state.winner_id) {
          const winner = state.players.find(p => p.user_id === state.winner_id);
          if (winner) {
            setWinnerName(winner.username);
            setShowWinnerModal(true);
          }
        }
      } else if (data.type === "game_over") {
        // Double check winner display
        const winner = gameState?.players.find(p => p.user_id === data.winner_id);
        if (winner) {
          setWinnerName(winner.username);
          setShowWinnerModal(true);
        }
      } else if (data.type === "invalid_action") {
        alert(data.message || "Invalid move!");
      } else if (data.type === "error") {
        setError(data.message);
      }
    };

    socket.onclose = () => {
      setWsConnected(false);
    };

    socket.onerror = () => {
      setError("Disconnected from game server.");
      setWsConnected(false);
    };

    return () => {
      if (socket) socket.close();
    };
  }, [myUserId, roomId]);

  // Scroll game log to bottom
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [gameState?.game_log]);

  const sendAction = (action: string, amount: number = 0) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ action, amount }));
    }
  };

  const getSuitSymbol = (suit: string) => {
    switch (suit.toLowerCase()) {
      case "h": return "♥";
      case "d": return "♦";
      case "c": return "♣";
      case "s": return "♠";
      default: return "";
    }
  };

  const getSuitColorClass = (suit: string) => {
    const s = suit.toLowerCase();
    return s === "h" || s === "d" ? "card-red" : "card-black";
  };

  if (!gameState || myUserId === null) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-[#121214]">
        {error ? (
          <div className="text-center p-6 max-w-md">
            <ShieldAlert className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-white mb-2">Tournament Error</h2>
            <p className="text-sm text-gray-400 mb-6">{error}</p>
            <button onClick={() => router.push("/dashboard")} className="gold-btn w-full">
              BACK TO LOBBY
            </button>
          </div>
        ) : (
          <div className="text-center">
            <RefreshCw className="w-8 h-8 animate-spin text-yellow-500 mx-auto mb-2" />
            <span className="text-gray-400 text-sm">Entering Sit & Go Poker Room...</span>
          </div>
        )}
      </div>
    );
  }

  // Find my seat index
  const mePlayer = gameState.players.find(p => p.user_id === myUserId);
  const mySeat = mePlayer?.seat_index ?? 0;
  const isMyTurn = gameState.current_turn_index === mySeat && gameState.betting_round !== "showdown";

  // Calculate my actions
  const myCurrentBet = mePlayer?.current_bet ?? 0;
  const myChips = mePlayer?.chips ?? 0;
  const callAmount = gameState.current_bet - myCurrentBet;
  const canCheck = callAmount === 0;

  // Render player seat positions based on relative seat mapping
  // Rel 0 = Bottom (Me)
  // Rel 1 = Right
  // Rel 2 = Top
  // Rel 3 = Left
  const getSeatPositionClass = (relIndex: number) => {
    switch (relIndex) {
      case 0: return "absolute bottom-[-50px] left-1/2 -translate-x-1/2";
      case 1: return "absolute right-[-70px] top-1/2 -translate-y-1/2";
      case 2: return "absolute top-[-50px] left-1/2 -translate-x-1/2";
      case 3: return "absolute left-[-70px] top-1/2 -translate-y-1/2";
      default: return "";
    }
  };

  return (
    <div className="fixed inset-0 bg-[#121214] flex flex-col h-screen w-screen overflow-hidden select-none z-50">
      {/* Header Info */}
      <header className="border-b border-white/5 bg-[#121214]/80 backdrop-blur-md px-6 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              if (confirm("Are you sure you want to leave the game? You will sit out and auto-fold.")) {
                router.push("/dashboard");
              }
            }}
            className="text-gray-400 hover:text-white transition"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="font-bold text-sm tracking-wider text-white">SIT & GO #{roomId.substring(0, 8).toUpperCase()}</h1>
            <p className="text-[10px] text-gray-500">Blinds: {gameState.small_blind}/{gameState.big_blind} • Hand #{gameState.hand_count}</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 font-semibold text-xs">
            <Coins className="w-3.5 h-3.5" />
            <span>Prize Pool: 3,600 Chips</span>
          </div>

          {!wsConnected && (
            <div className="text-xs text-red-400 font-bold animate-pulse flex items-center gap-1">
              <ShieldAlert className="w-3 h-3" /> Reconnecting...
            </div>
          )}
        </div>
      </header>

      {/* Main Table Area */}
      <div className="flex-1 relative flex items-center justify-center py-4 px-8 overflow-hidden bg-radial from-[#151c18] to-[#0c0d10]">
        
        {/* Felt Poker Table */}
        <div className="poker-felt-table flex flex-col items-center justify-center">
          
          {/* Table Logo */}
          <div className="absolute text-emerald-800/10 text-4xl font-extrabold select-none tracking-widest text-center">
            ROYAL<br/>HOLD'EM
          </div>

          {/* Pot Display */}
          {gameState.pot > 0 && (
            <div className="z-10 px-4 py-2 rounded-lg bg-black/60 border border-yellow-500/30 text-yellow-400 font-bold text-sm shadow-lg flex flex-col items-center select-none mb-3">
              <span className="text-[10px] text-gray-400 uppercase tracking-widest font-semibold">Total Pot</span>
              <span>{gameState.pot} Chips</span>
            </div>
          )}

          {/* Community Cards */}
          <div className="flex gap-2 z-10 min-h-[72px]">
            {gameState.community_cards.map((card, idx) => (
              <div
                key={idx}
                className={`poker-card card-dealt card-flipped ${getSuitColorClass(card.suit)}`}
              >
                <div className="text-sm">{card.rank}</div>
                <div className="text-xl self-end leading-none">{getSuitSymbol(card.suit)}</div>
              </div>
            ))}
            {Array.from({ length: 5 - gameState.community_cards.length }).map((_, idx) => (
              <div key={idx} className="w-[50px] h-[72px] rounded-lg border border-white/10 bg-black/20" />
            ))}
          </div>

          {/* Players Seats */}
          {gameState.players.map((p) => {
            const relIndex = (p.seat_index - mySeat + 4) % 4;
            const isTurn = gameState.current_turn_index === p.seat_index && gameState.betting_round !== "showdown";
            const dealerBtnIndex = gameState.dealer_index;

            return (
              <div key={p.user_id} className={`${getSeatPositionClass(relIndex)} z-20`}>
                <div className="flex flex-col items-center relative">
                  
                  {/* Dealer Button Indicator */}
                  {dealerBtnIndex === p.seat_index && (
                    <div className="absolute -top-3 -right-3 w-6 h-6 rounded-full bg-white text-black border border-gray-300 font-extrabold text-[10px] flex items-center justify-center shadow-lg select-none">
                      D
                    </div>
                  )}

                  {/* Player Pocket Cards */}
                  <div className="flex gap-1 mb-2 select-none h-[72px]">
                    {p.cards.map((card, cIdx) => (
                      <div
                        key={cIdx}
                        className={`poker-card card-dealt ${
                          card.rank === "?" ? "card-back" : `${getSuitColorClass(card.suit)} card-flipped`
                        }`}
                      >
                        {card.rank !== "?" && (
                          <>
                            <div className="text-xs">{card.rank}</div>
                            <div className="text-lg self-end leading-none">{getSuitSymbol(card.suit)}</div>
                          </>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Player Node Frame */}
                  <div
                    className={`w-32 py-2 px-3 rounded-xl border glass-panel flex flex-col items-center text-center shadow-md relative transition-all ${
                      isTurn
                        ? "border-yellow-500 shadow-[0_0_15px_rgba(212,175,55,0.4)] animate-[active-player-pulse_1.5s_infinite]"
                        : "border-white/10"
                    } ${p.is_folded ? "opacity-50" : ""}`}
                  >
                    <span className="font-bold text-xs text-white truncate max-w-full">{p.username}</span>
                    <span className="text-[10px] text-yellow-500 font-semibold mt-0.5">{p.chips <= 0 ? "ALL-IN" : `${p.chips.toLocaleString()} Chp`}</span>
                    
                    {!p.is_connected && (
                      <span className="absolute -top-2.5 bg-red-500 text-white font-extrabold text-[8px] px-1.5 py-0.5 rounded uppercase tracking-wider scale-90">
                        DISCONNECT
                      </span>
                    )}

                    {p.last_action && (
                      <span className={`absolute -bottom-3 px-2 py-0.5 rounded text-[8px] font-bold uppercase tracking-wider border shadow-md ${
                        p.last_action.includes("Fold") ? "bg-red-950 text-red-300 border-red-900" :
                        p.last_action.includes("Check") ? "bg-zinc-800 text-zinc-300 border-zinc-700" :
                        p.last_action.includes("Raise") ? "bg-yellow-950 text-yellow-300 border-yellow-800" :
                        "bg-green-950 text-green-300 border-green-900"
                      }`}>
                        {p.last_action}
                      </span>
                    )}

                    {p.hand_description && (
                      <span className="absolute -top-3.5 bg-blue-900 border border-blue-700 text-white text-[9px] font-bold px-2 py-0.5 rounded">
                        {p.hand_description}
                      </span>
                    )}
                  </div>

                  {/* Current Bet chips stack in front of player */}
                  {p.current_bet > 0 && (
                    <div className={`absolute font-bold text-[10px] text-yellow-500 bg-black/60 border border-yellow-500/20 px-2 py-0.5 rounded-full flex items-center gap-1 shadow-sm ${
                      relIndex === 0 ? "-top-8" :
                      relIndex === 1 ? "left-[-80px]" :
                      relIndex === 2 ? "-bottom-8" :
                      "right-[-80px]"
                    }`}>
                      <div className="w-2 h-2 rounded-full bg-yellow-500" />
                      <span>{p.current_bet}</span>
                    </div>
                  )}

                </div>
              </div>
            );
          })}

        </div>

      </div>

      {/* Footer Controls & Log Panel */}
      <footer className="border-t border-white/5 bg-[#17171a] p-4 flex gap-4 shrink-0 max-h-[220px]">
        {/* Left Side: Game Action Console Logs */}
        <div className="flex-1 glass-panel border border-white/5 p-3 flex flex-col h-full min-w-0">
          <div className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest mb-1.5 shrink-0">Game Console</div>
          <div
            ref={logContainerRef}
            className="flex-1 overflow-y-auto text-xs space-y-1 pr-2 text-gray-400 select-text font-mono"
          >
            {gameState.game_log.map((log, idx) => (
              <div key={idx} className={
                log.includes("wins") ? "text-green-400 font-semibold" :
                log.includes("posts") ? "text-zinc-500" :
                log.includes("dealt") || log.includes("Flop") || log.includes("Turn") || log.includes("River") ? "text-blue-400 font-bold" :
                log.includes("ALL-IN") ? "text-red-400 font-semibold" :
                "text-gray-300"
              }>
                {log}
              </div>
            ))}
          </div>
        </div>

        {/* Right Side: Action Controls Panel */}
        <div className="w-[380px] shrink-0 flex flex-col justify-center gap-3">
          {isMyTurn ? (
            <>
              {/* Betting / Raise Slider */}
              {myChips > 0 && (
                <div className="flex items-center gap-3 bg-black/40 border border-white/5 rounded-lg px-4 py-2 text-sm">
                  <span className="text-xs text-gray-400 font-medium">Raise:</span>
                  <input
                    type="range"
                    min={Math.min(gameState.min_raise, myChips + myCurrentBet)}
                    max={myChips + myCurrentBet}
                    step={10}
                    value={raiseAmount}
                    onChange={(e) => setRaiseAmount(Number(e.target.value))}
                    className="flex-1 h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-yellow-500"
                  />
                  <span className="font-bold text-yellow-500 w-16 text-right">{raiseAmount}</span>
                </div>
              )}

              {/* Action Buttons Grid */}
              <div className="grid grid-cols-3 gap-2">
                <button
                  onClick={() => sendAction("fold")}
                  className="action-btn active-fold py-3 text-red-400 border-red-950/40 hover:border-red-500/30"
                >
                  FOLD
                </button>

                <button
                  onClick={() => sendAction(canCheck ? "check" : "call")}
                  className="action-btn py-3 border-zinc-700 text-white font-semibold"
                >
                  {canCheck ? "CHECK" : `CALL ${callAmount}`}
                </button>

                <button
                  onClick={() => sendAction("raise", raiseAmount)}
                  disabled={myChips <= 0 || raiseAmount < gameState.min_raise}
                  className="gold-btn py-3 text-sm"
                >
                  {raiseAmount >= myChips + myCurrentBet ? "ALL-IN" : `RAISE TO ${raiseAmount}`}
                </button>
              </div>
            </>
          ) : (
            <div className="h-full flex items-center justify-center p-6 border border-white/5 bg-black/10 rounded-xl text-sm text-gray-500 font-semibold tracking-wider text-center">
              {gameState.betting_round === "showdown" ? (
                <span>SHOWDOWN • NEXT HAND STARTING SHORTLY</span>
              ) : (
                <span>WAITING FOR OPPONENTS TO ACT...</span>
              )}
            </div>
          )}
        </div>
      </footer>

      {/* Winner Tournament Complete Modal */}
      {showWinnerModal && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-md flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-md p-8 glass-panel border border-yellow-500/20 text-center shadow-2xl relative">
            <div className="absolute top-0 left-0 w-full h-[4px] bg-gradient-to-r from-yellow-500 via-amber-400 to-yellow-500" />
            
            <div className="w-20 h-20 rounded-full bg-yellow-500/10 border border-yellow-500/30 flex items-center justify-center mx-auto mb-6 text-yellow-500">
              <Check className="w-10 h-10" />
            </div>

            <h2 className="text-2xl font-black text-white tracking-wide">TOURNAMENT COMPLETE</h2>
            
            <div className="my-6 p-4 rounded-xl bg-white/5 border border-white/5">
              <span className="text-xs text-gray-400 block uppercase tracking-wider mb-1 font-semibold">Champion</span>
              <span className="text-xl font-bold text-yellow-400">{winnerName}</span>
            </div>

            <p className="text-xs text-gray-400 mb-8 max-w-xs mx-auto leading-relaxed">
              Congratulations! The winner has been awarded the prize pool of 3,600 chips, and tournament results have been recorded.
            </p>

            <button
              onClick={() => {
                setShowWinnerModal(false);
                router.push("/dashboard");
              }}
              className="w-full gold-btn py-3.5 font-bold shadow-lg"
            >
              RETURN TO LOBBY
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
