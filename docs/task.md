# Task List - Sit & Go Texas Hold'em Poker

- [x] **Backend Setup**
  - [x] Create `backend/requirements.txt`
  - [x] Implement `backend/models.py` (SQLAlchemy models for User and Tournament)
  - [x] Implement `backend/evaluator.py` (7-card Texas Hold'em Hand Evaluator)
  - [x] Implement `backend/poker_logic.py` (Texas Hold'em rules, pot manager, side pots)
  - [x] Implement `backend/main.py` (FastAPI web server, Auth APIs, Lobby, WebSockets)
- [x] **Frontend Setup**
  - [x] Initialize Next.js app in `frontend/`
  - [x] Implement global styling and typography in `frontend/app/globals.css`
  - [x] Create components (Cards, Actions, Player Seats, Chat/Log, Stats Dashboard)
  - [x] Implement landing page and registration/login form (`frontend/app/page.tsx`)
  - [x] Implement user stats and dashboard (`frontend/app/dashboard/page.tsx`)
  - [x] Implement the Sit & Go Poker Room (`frontend/app/play/[roomId]/page.tsx`)
- [x] **Verification & Testing**
  - [x] Test Hand Evaluator with various hand types
  - [x] Verify 4-Player lobby matchmaking and game start lock
  - [x] Verify game rounds (Pre-flop, Flop, Turn, River, Showdown), chip deduction, and rake (10%)
  - [x] Play a complete 4-player game across separate browser sessions and verify win distribution
