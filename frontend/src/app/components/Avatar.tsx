import React from "react";

interface AvatarProps {
  avatarId: number;
  className?: string;
}

export default function Avatar({ avatarId, className = "w-10 h-10" }: AvatarProps) {
  // Safe bounds check
  const id = avatarId >= 1 && avatarId <= 8 ? avatarId : 1;

  // Svg assets mapping
  switch (id) {
    case 1: // Spade (Black & Gold)
      return (
        <svg viewBox="0 0 100 100" className={`${className} select-none`} xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="spadeBg" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#1e1e24" />
              <stop offset="100%" stopColor="#08080a" />
            </linearGradient>
            <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#f3cf58" />
              <stop offset="50%" stopColor="#d4af37" />
              <stop offset="100%" stopColor="#aa7c11" />
            </linearGradient>
          </defs>
          <circle cx="50" cy="50" r="46" fill="url(#spadeBg)" stroke="url(#goldGrad)" strokeWidth="3" />
          {/* Spade Path */}
          <path
            d="M 50,22 C 45,37 26,42 26,60 C 26,73 37,78 50,67 C 63,78 74,73 74,60 C 74,42 55,37 50,22 Z M 47,65 L 42,78 H 58 L 53,65 Z"
            fill="url(#goldGrad)"
          />
        </svg>
      );
    case 2: // Heart (Crimson & Gold)
      return (
        <svg viewBox="0 0 100 100" className={`${className} select-none`} xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="heartBg" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#4a0e17" />
              <stop offset="100%" stopColor="#150305" />
            </linearGradient>
            <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#f3cf58" />
              <stop offset="50%" stopColor="#d4af37" />
              <stop offset="100%" stopColor="#aa7c11" />
            </linearGradient>
          </defs>
          <circle cx="50" cy="50" r="46" fill="url(#heartBg)" stroke="url(#goldGrad)" strokeWidth="3" />
          {/* Heart Path */}
          <path
            d="M 50,32 C 50,32 37,18 25,29 C 14,40 25,58 50,78 C 75,58 86,40 75,29 C 63,18 50,32 50,32 Z"
            fill="url(#goldGrad)"
          />
        </svg>
      );
    case 3: // Diamond (Amber & Gold)
      return (
        <svg viewBox="0 0 100 100" className={`${className} select-none`} xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="diamondBg" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#1a2e40" />
              <stop offset="100%" stopColor="#0a121a" />
            </linearGradient>
            <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#f3cf58" />
              <stop offset="50%" stopColor="#d4af37" />
              <stop offset="100%" stopColor="#aa7c11" />
            </linearGradient>
          </defs>
          <circle cx="50" cy="50" r="46" fill="url(#diamondBg)" stroke="url(#goldGrad)" strokeWidth="3" />
          {/* Diamond Path */}
          <path d="M 50,20 L 76,50 L 50,80 L 24,50 Z" fill="url(#goldGrad)" />
        </svg>
      );
    case 4: // Club (Emerald & Gold)
      return (
        <svg viewBox="0 0 100 100" className={`${className} select-none`} xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="clubBg" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#082b15" />
              <stop offset="100%" stopColor="#020d06" />
            </linearGradient>
            <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#f3cf58" />
              <stop offset="50%" stopColor="#d4af37" />
              <stop offset="100%" stopColor="#aa7c11" />
            </linearGradient>
          </defs>
          <circle cx="50" cy="50" r="46" fill="url(#clubBg)" stroke="url(#goldGrad)" strokeWidth="3" />
          {/* Club Path */}
          <path
            d="M 50,44 C 55,44 59,40 59,35 C 59,30 55,26 50,26 C 45,26 41,30 41,35 C 41,40 45,44 50,44 Z M 37,60 C 42,60 46,56 46,51 C 46,46 42,42 37,42 C 32,42 28,46 28,51 C 28,56 32,60 37,60 Z M 63,60 C 68,60 72,56 72,51 C 72,46 68,42 63,42 C 58,42 54,46 54,51 C 54,56 58,60 63,60 Z M 48,56 L 43,76 H 57 L 52,56 Z"
            fill="url(#goldGrad)"
          />
        </svg>
      );
    case 5: // Crown (Royal Purple & Gold)
      return (
        <svg viewBox="0 0 100 100" className={`${className} select-none`} xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="crownBg" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#3b0f5c" />
              <stop offset="100%" stopColor="#10031c" />
            </linearGradient>
            <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#f3cf58" />
              <stop offset="50%" stopColor="#d4af37" />
              <stop offset="100%" stopColor="#aa7c11" />
            </linearGradient>
          </defs>
          <circle cx="50" cy="50" r="46" fill="url(#crownBg)" stroke="url(#goldGrad)" strokeWidth="3" />
          {/* Crown Path */}
          <path
            d="M 24,70 L 76,70 L 80,42 L 65,54 L 50,30 L 35,54 L 20,42 Z M 24,73 H 76 V 77 H 24 Z"
            fill="url(#goldGrad)"
          />
          <circle cx="50" cy="27" r="3" fill="url(#goldGrad)" />
          <circle cx="20" cy="39" r="2.5" fill="url(#goldGrad)" />
          <circle cx="80" cy="39" r="2.5" fill="url(#goldGrad)" />
        </svg>
      );
    case 6: // Star (Sapphire & Gold)
      return (
        <svg viewBox="0 0 100 100" className={`${className} select-none`} xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="starBg" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#0f2b5c" />
              <stop offset="100%" stopColor="#030c1c" />
            </linearGradient>
            <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#f3cf58" />
              <stop offset="50%" stopColor="#d4af37" />
              <stop offset="100%" stopColor="#aa7c11" />
            </linearGradient>
          </defs>
          <circle cx="50" cy="50" r="46" fill="url(#starBg)" stroke="url(#goldGrad)" strokeWidth="3" />
          {/* Star Path */}
          <path
            d="M 50,20 L 59,41 L 82,43 L 64,58 L 70,80 L 50,68 L 30,80 L 36,58 L 18,43 L 41,41 Z"
            fill="url(#goldGrad)"
          />
        </svg>
      );
    case 7: // Gold Coin (Yellow & Bronze)
      return (
        <svg viewBox="0 0 100 100" className={`${className} select-none`} xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="coinBg" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#5c450f" />
              <stop offset="100%" stopColor="#1c1403" />
            </linearGradient>
            <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#f3cf58" />
              <stop offset="50%" stopColor="#d4af37" />
              <stop offset="100%" stopColor="#aa7c11" />
            </linearGradient>
          </defs>
          <circle cx="50" cy="50" r="46" fill="url(#coinBg)" stroke="url(#goldGrad)" strokeWidth="3" />
          <circle cx="50" cy="50" r="38" fill="none" stroke="url(#goldGrad)" strokeWidth="2" strokeDasharray="4 3" />
          {/* Coin Dollar Symbol */}
          <path
            d="M 50,28 V 72 M 45,35 H 55 C 59,35 60,38 60,41 C 60,45 57,47 50,49 C 43,51 40,53 40,58 C 40,62 42,65 50,65 H 55 M 40,38 H 50"
            fill="none"
            stroke="url(#goldGrad)"
            strokeWidth="4"
            strokeLinecap="round"
          />
        </svg>
      );
    case 8: // Poker Chip (Classic Red & White)
      return (
        <svg viewBox="0 0 100 100" className={`${className} select-none`} xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="chipBg" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#8c111c" />
              <stop offset="100%" stopColor="#300307" />
            </linearGradient>
            <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#f3cf58" />
              <stop offset="50%" stopColor="#d4af37" />
              <stop offset="100%" stopColor="#aa7c11" />
            </linearGradient>
          </defs>
          <circle cx="50" cy="50" r="46" fill="url(#chipBg)" stroke="url(#goldGrad)" strokeWidth="3" />
          {/* Outer Stripes */}
          <g stroke="#ffffff" strokeWidth="4" strokeLinecap="round" opacity="0.8">
            <line x1="50" y1="7" x2="50" y2="15" />
            <line x1="50" y1="85" x2="50" y2="93" />
            <line x1="7" y1="50" x2="15" y2="50" />
            <line x1="85" y1="50" x2="93" y2="50" />
            <line x1="20" y1="20" x2="26" y2="26" />
            <line x1="74" y1="74" x2="80" y2="80" />
            <line x1="74" y1="20" x2="80" y2="26" />
            <line x1="20" y1="74" x2="26" y2="80" />
          </g>
          <circle cx="50" cy="50" r="28" fill="none" stroke="url(#goldGrad)" strokeWidth="2.5" />
          {/* Crown inside chip */}
          <path
            d="M 38,58 L 62,58 L 64,44 L 57,50 L 50,38 L 43,50 L 36,44 Z"
            fill="url(#goldGrad)"
          />
        </svg>
      );
    default:
      return null;
  }
}
