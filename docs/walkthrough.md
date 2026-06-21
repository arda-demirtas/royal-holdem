# Walkthrough - Sit & Go Texas Hold'em Poker Game

We have fully implemented a premium, real-time multiplayer Texas Hold'em poker Sit & Go tournament game using a **FastAPI** backend (SQLAlchemy + SQLite) and a **Next.js** frontend with a custom, high-end dark luxury aesthetic.

---

## What's New: Cryptocurrency Integration

We have added a gorgeous, fully integrated cryptocurrency payment simulation for buying chips:
- **USDT (Tether on TRC-20)**: $10 USD = 10 USDT = 10,000 Chips.
- **Solana (SOL)**: The backend fetches the **live SOL price in USD** using the public CoinGecko API and automatically calculates the exact amount of SOL required (e.g. `$10 / SOL_price = 0.0625 SOL`).
- **QR Codes**: Renders a scannable payment QR code dynamically using a public QR service.
- **Blockchain Verification Simulation**: When the user clicks "Verify Deposit", the app simulates a blockchain transaction scan (showing a loading spinner for 2.5 seconds) and then calls the backend to credit the chips to the user's SQLite record.

---

## Detailed Changes Made

### 1. Backend Component (`backend/`)
- [requirements.txt](file:///c:/Users/h1z1a/Desktop/oyun/backend/requirements.txt): Declared all Python dependencies.
- [models.py](file:///c:/Users/h1z1a/Desktop/oyun/backend/models.py): Database schemas for `User` and `TournamentRecord`.
- [evaluator.py](file:///c:/Users/h1z1a/Desktop/oyun/backend/evaluator.py): Pure-Python 7-card hand strength evaluator.
- [poker_logic.py](file:///c:/Users/h1z1a/Desktop/oyun/backend/poker_logic.py): Core game engine (Pre-flop -> Flop -> Turn -> River -> Showdown, blinds double every 5 hands, multi-way side pots).
- [main.py](file:///c:/Users/h1z1a/Desktop/oyun/backend/main.py): FastAPI server containing Auth APIs, matchmaking, gameplay WebSockets, and **crypto payment APIs** (`/api/crypto/create-payment`, `/api/crypto/verify-payment`, and live price lookup via CoinGecko).
- [test_evaluator.py](file:///c:/Users/h1z1a/Desktop/oyun/backend/test_evaluator.py): Unit tests verifying the hand evaluator.

### 2. Frontend Component (`frontend/`)
- [package.json](file:///c:/Users/h1z1a/Desktop/oyun/frontend/package.json): Added Lucide icons.
- [globals.css](file:///c:/Users/h1z1a/Desktop/oyun/frontend/src/app/globals.css): Styled the custom green felt poker table (scaled down to 330px height with media queries to fit viewports without scrolling), playing cards, gold buttons, and glassmorphism.
- [layout.tsx](file:///c:/Users/h1z1a/Desktop/oyun/frontend/src/app/layout.tsx): Set document metadata and title to **Royal Hold'em - Sit & Go Poker**.
- [page.tsx](file:///c:/Users/h1z1a/Desktop/oyun/frontend/src/app/page.tsx): Login and registration forms.
- [dashboard/page.tsx](file:///c:/Users/h1z1a/Desktop/oyun/frontend/src/app/dashboard/page.tsx): User dashboard displaying stats, claiming free chips, matchmaking lobby, and the **new Buy Chips Crypto Modal** with package selection, QR codes, and blockchain check simulations.
- [play/\[roomId\]/page.tsx](file:///c:/Users/h1z1a/Desktop/oyun/frontend/src/app/play/%5BroomId%5D/page.tsx): Virtual poker table room with relative seats, game logs, and actions bar (locked to viewport height to prevent scrolls).

---

## Verification & Testing

### 1. Hand Evaluator Tests
Run unit tests checking all poker hand rankings:
```bash
python backend/test_evaluator.py
```
*Output: ALL TESTS PASSED!*

### 2. Running the Servers
Both servers are running in the background:
- **Backend (FastAPI)**: Running on `http://127.0.0.1:8000`
- **Frontend (Next.js)**: Running on `http://localhost:3000`

---

## How to Play and Verify

### A. How to Buy Chips with Crypto:
1. Log in and go to the Dashboard page.
2. Click **BUY CHIPS** in the top-right header.
3. Select a package (e.g. **10k Chips** for $10 USD).
4. Choose a cryptocurrency: **Tether (USDT)** or **Solana (SOL)**.
5. Click **Generate Payment**.
   - Notice the system displays the scannable QR code.
   - Notice the exact crypto amount: for Solana, it fetches the live SOL price and displays e.g. `0.0625 SOL`.
6. Click **Verify Deposit**. The app displays a simulated blockchain verification step for 2.5 seconds, then credits the chips and updates your dashboard header balance immediately!

### B. How to Play a Match:
1. Open **4 different browser sessions** (e.g. tarayıcı profilleri veya farklı tarayıcılar) and navigate to `http://localhost:3000`.
2. Register/login as 4 players.
3. In each window, click **Join Sit & Go Lobby**.
4. Once the 4th player joins:
   - Each player is deducted **1,000 chips** (10% rake is taken, winner takes all **3,600 chips**).
   - All 4 windows are redirected to the play screen.
5. Play through Pre-flop, Flop, Turn, River, and Showdown.
6. The winner receives the **3,600 chips** prize pool.
