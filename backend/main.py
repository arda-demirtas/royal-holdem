import os
import asyncio
import uuid
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import bcrypt

from models import Base, User, TournamentRecord, ProcessedTransaction
from poker_logic import PokerGame, Player

# Configurations
SECRET_KEY = "SUPER_SECRET_POKER_KEY_CHANGE_THIS"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 1 day

DATABASE_URL = "sqlite:///./poker.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sit & Go Poker Backend")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify Next.js host
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic schemas
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserProfile(BaseModel):
    id: int
    username: str
    email: str
    chips: int
    games_played: int
    games_won: int
    hands_played: int
    hands_won: int
    win_rate: float
    hand_win_rate: float

# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user_from_token(token: str, db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# REST Endpoints
@app.post("/api/register", response_model=Token)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    # Check if username or email already exists
    db_user = db.query(User).filter((User.username == user_in.username) | (User.email == user_in.email)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username or Email already registered")
    
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        chips=100000  # Start chips
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = create_access_token(data={"sub": new_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user_in.username).first()
    if not db_user or not verify_password(user_in.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/profile", response_model=UserProfile)
def get_profile(token: str = Query(...), db: Session = Depends(get_db)):
    user = get_current_user_from_token(token, db)
    return UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        chips=user.chips,
        games_played=user.games_played,
        games_won=user.games_won,
        hands_played=user.hands_played,
        hands_won=user.hands_won,
        win_rate=user.win_rate,
        hand_win_rate=user.hand_win_rate
    )

@app.post("/api/claim-free-chips")
def claim_free_chips(token: str = Query(...), db: Session = Depends(get_db)):
    user = get_current_user_from_token(token, db)
    if user.chips < 1000:
        user.chips = 5000
        db.commit()
        return {"message": "Claimed 5,000 chips!", "chips": user.chips}
    raise HTTPException(status_code=400, detail="You must have less than 1,000 chips to claim free chips.")


# Lobby Matchmaking Logic
class Matchmaker:
    def __init__(self):
        # Maps connection (WebSocket) to user_id
        self.connections: Dict[WebSocket, int] = {}
        # Maps user_id to username
        self.user_names: Dict[int, str] = {}
        # Active queue
        self.queue: List[WebSocket] = []

    async def add(self, ws: WebSocket, user_id: int, username: str):
        # Prevent duplicate entries in queue
        for existing_ws, uid in list(self.connections.items()):
            if uid == user_id:
                # Disconnect the old lobby connection
                try:
                    await existing_ws.close()
                except Exception:
                    pass
                self.connections.pop(existing_ws, None)
                if existing_ws in self.queue:
                    self.queue.remove(existing_ws)

        self.connections[ws] = user_id
        self.user_names[user_id] = username
        self.queue.append(ws)
        await self.broadcast_lobby_status()
        await self.check_match()

    def remove(self, ws: WebSocket):
        if ws in self.connections:
            user_id = self.connections.pop(ws)
            self.user_names.pop(user_id, None)
        if ws in self.queue:
            self.queue.remove(ws)
        asyncio.create_task(self.broadcast_lobby_status())

    async def broadcast_lobby_status(self):
        count = len(self.queue)
        users_list = [self.user_names[self.connections[ws]] for ws in self.queue]
        for ws in self.queue:
            try:
                await ws.send_json({
                    "type": "lobby_status",
                    "players_count": count,
                    "players": users_list
                })
            except Exception:
                pass

    async def check_match(self):
        # We need exactly 4 players
        if len(self.queue) >= 4:
            matched_ws = self.queue[:4]
            self.queue = self.queue[4:]

            matched_players = []
            for ws in matched_ws:
                uid = self.connections.pop(ws)
                uname = self.user_names.pop(uid)
                matched_players.append((ws, uid, uname))

            # Deduct buy-in of 1,000 chips from each user database
            db = SessionLocal()
            valid_match = True
            for ws, uid, uname in matched_players:
                user = db.query(User).filter(User.id == uid).first()
                if not user or user.chips < 1000:
                    valid_match = False
                    # Send error to this specific player and close
                    try:
                        await ws.send_json({"type": "error", "message": "Ineligible chips balance (Need 1,000 chips)"})
                        await ws.close()
                    except Exception:
                        pass
                
            if not valid_match:
                db.close()
                # Put back the eligible players in queue
                for ws, uid, uname in matched_players:
                    user = db.query(User).filter(User.id == uid).first()
                    if user and user.chips >= 1000:
                        await self.add(ws, uid, uname)
                return

            # Perform chips deduction & create tournament history
            tournament_id = str(uuid.uuid4())
            buy_in = 1000
            rake = 100  # 10% rake
            prize_pool = 3600  # (1000 - 100) * 4

            # Create tournament record
            tour_rec = TournamentRecord(
                id=tournament_id,
                buy_in=buy_in,
                rake=rake * 4,
                prize_pool=prize_pool,
                winner_id=None
            )
            db.add(tour_rec)

            players_for_game = []
            for i, (ws, uid, uname) in enumerate(matched_players):
                user = db.query(User).filter(User.id == uid).first()
                user.chips -= buy_in
                user.games_played += 1
                players_for_game.append(Player(user_id=uid, username=uname, chips=2000, seat_index=i))

            db.commit()
            db.close()

            # Create game
            game = PokerGame(tournament_id, players_for_game)
            ACTIVE_GAMES[tournament_id] = game
            game.start_game()

            # Notify all 4 matched players
            for ws, uid, uname in matched_players:
                try:
                    await ws.send_json({
                        "type": "match_found",
                        "tournament_id": tournament_id
                    })
                    await ws.close()
                except Exception:
                    pass

matchmaker = Matchmaker()
ACTIVE_GAMES: Dict[str, PokerGame] = {}
# Active WebSocket connections for poker tables: tournament_id -> list of WS
GAME_SOCKETS: Dict[str, Set[WebSocket]] = {}
# Maps WebSocket to (tournament_id, user_id)
SOCKET_TO_PLAYER: Dict[WebSocket, Tuple[str, int]] = {}

@app.websocket("/ws/lobby")
async def ws_lobby(websocket: WebSocket, token: str = Query(...)):
    await websocket.accept()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except Exception:
        await websocket.send_json({"type": "error", "message": "Invalid auth token"})
        await websocket.close()
        return

    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user:
        db.close()
        await websocket.close()
        return

    if user.chips < 1000:
        db.close()
        await websocket.send_json({"type": "error", "message": "You need at least 1,000 chips to enter Sit & Go"})
        await websocket.close()
        return

    user_id = user.id
    username_val = user.username
    db.close()

    await matchmaker.add(websocket, user_id, username_val)

    try:
        while True:
            # Keep connection alive, listen for ping/disconnect
            await websocket.receive_text()
    except WebSocketDisconnect:
        matchmaker.remove(websocket)

async def broadcast_game_state(tournament_id: str):
    game = ACTIVE_GAMES.get(tournament_id)
    if not game:
        return
    sockets = GAME_SOCKETS.get(tournament_id, set())
    
    for ws in list(sockets):
        details = SOCKET_TO_PLAYER.get(ws)
        if not details:
            continue
        uid = details[1]
        try:
            # We only show the cards of the current player, unless it's showdown
            await ws.send_json({
                "type": "game_state",
                "state": game.to_dict(current_user_id=uid)
            })
        except Exception:
            pass

async def handle_game_continuation(tournament_id: str):
    """
    Called after a hand completes. Wait 5 seconds, then deal next hand.
    """
    await asyncio.sleep(5)
    game = ACTIVE_GAMES.get(tournament_id)
    if not game:
        return
    
    db = SessionLocal()
    
    # Check if hand winners won hands in the DB
    # We can check who won the pots.
    # In poker_logic.py, we evaluate who wins, but we can also just record stats when they win hands.
    # Let's count who got hand wins.
    # We can identify hand wins from hand outcome:
    # Any player whose chips increased in the showdown can be credited a hand win!
    # Let's keep a record of chips before hand start, or track hand winners.
    # In this case, we can increment user.hands_played for all active players in this hand, and user.hands_won for the hand winners.
    active_players = [p for p in game.players if p.chips > 0 or p.chips_in_pot > 0]
    for p in active_players:
        user = db.query(User).filter(User.id == p.user_id).first()
        if user:
            user.hands_played += 1
    
    # Start new hand
    game.start_new_hand()
    
    if game.betting_round == "finished":
        # Game finished, winner decided!
        winner_id = game.winner_id
        if winner_id:
            # Award prize pool (3600 chips) to winner
            winner_user = db.query(User).filter(User.id == winner_id).first()
            if winner_user:
                winner_user.chips += 3600
                winner_user.games_won += 1
            
            # Update tournament record in db
            tour_record = db.query(TournamentRecord).filter(TournamentRecord.id == tournament_id).first()
            if tour_record:
                tour_record.winner_id = winner_id

        db.commit()
        db.close()
        
        # Notify clients that game is finished
        sockets = GAME_SOCKETS.get(tournament_id, set())
        for ws in list(sockets):
            try:
                await ws.send_json({"type": "game_over", "winner_id": winner_id})
            except Exception:
                pass
            
        # Clean up game
        ACTIVE_GAMES.pop(tournament_id, None)
        GAME_SOCKETS.pop(tournament_id, None)
        return

    db.commit()
    db.close()
    await broadcast_game_state(tournament_id)

@app.websocket("/ws/play/{tournament_id}")
async def ws_play(websocket: WebSocket, tournament_id: str, token: str = Query(...)):
    await websocket.accept()
    
    # Auth user
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except Exception:
        await websocket.send_json({"type": "error", "message": "Invalid auth token"})
        await websocket.close()
        return

    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    if not user:
        await websocket.close()
        return

    # Check if game exists
    game = ACTIVE_GAMES.get(tournament_id)
    if not game:
        await websocket.send_json({"type": "error", "message": "Tournament not found or finished"})
        await websocket.close()
        return

    # Find the corresponding player in game
    player = None
    for p in game.players:
        if p.user_id == user.id:
            player = p
            break

    if not player:
        await websocket.send_json({"type": "error", "message": "You are not a player in this tournament"})
        await websocket.close()
        return

    # Store connection
    player.is_connected = True
    GAME_SOCKETS.setdefault(tournament_id, set()).add(websocket)
    SOCKET_TO_PLAYER[websocket] = (tournament_id, user.id)

    # Log connection
    game.log(f"{player.username} reconnected")
    await broadcast_game_state(tournament_id)

    try:
        while True:
            data = await websocket.receive_json()
            # Handle action
            action = data.get("action")  # 'fold', 'check', 'call', 'raise'
            amount = data.get("amount", 0)

            if action:
                success = game.process_action(user.id, action, amount)
                if success:
                    await broadcast_game_state(tournament_id)
                    
                    # If showdown is reached, schedule next round transition in background
                    if game.betting_round == "showdown":
                        asyncio.create_task(handle_game_continuation(tournament_id))
                else:
                    try:
                        await websocket.send_json({"type": "invalid_action", "message": "Illegal move or not your turn"})
                    except Exception:
                        pass
    except WebSocketDisconnect:
        # Player disconnected
        player.is_connected = False
        sockets = GAME_SOCKETS.get(tournament_id, set())
        if websocket in sockets:
            sockets.remove(websocket)
        SOCKET_TO_PLAYER.pop(websocket, None)
        game.log(f"{player.username} disconnected")

        # If it's this player's turn, auto-fold them to keep the game going
        if game.current_turn_index == player.seat_index and game.betting_round not in ["showdown", "finished", "waiting"]:
            # Auto fold or check if check is free
            action = "check" if player.current_bet == game.current_bet else "fold"
            game.process_action(player.user_id, action)
            await broadcast_game_state(tournament_id)
            if game.betting_round == "showdown":
                asyncio.create_task(handle_game_continuation(tournament_id))
        else:
            await broadcast_game_state(tournament_id)

# Wallet Configurations
SOL_WALLET_ADDRESS = "6qUJPTYPYFVPRCqAWuvGYC93nQe9mMSvmEPXFRNyLdPG"
USDT_WALLET_ADDRESS = "TYAzaEGzVoZiZAiZwTKa9ZVU1iUfHy6Jsg"

# Global pending payments cache
PENDING_PAYMENTS: Dict[str, dict] = {}

def get_sol_price() -> float:
    try:
        import urllib.request
        import json
        url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            return float(data["solana"]["usd"])
    except Exception:
        return 160.0  # Fallback price

def verify_solana_transaction(tx_signature: str, target_address: str, expected_sol_amount: float) -> bool:
    import urllib.request
    import json
    url = "https://api.mainnet-beta.solana.com"
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [
            tx_signature,
            {"encoding": "json", "maxSupportedTransactionVersion": 0}
        ]
    }
    
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode())
            result = res_data.get("result")
            if not result:
                return False
                
            # Check if transaction failed
            meta = result.get("meta", {})
            if not meta or meta.get("err") is not None:
                return False
                
            # Verify destination wallet and balance changes
            transaction = result.get("transaction", {})
            message = transaction.get("message", {})
            account_keys = message.get("accountKeys", [])
            
            try:
                target_idx = account_keys.index(target_address)
            except ValueError:
                return False  # Target wallet not involved
                
            pre_balances = meta.get("preBalances", [])
            post_balances = meta.get("postBalances", [])
            
            if len(pre_balances) <= target_idx or len(post_balances) <= target_idx:
                return False
                
            received_lamports = post_balances[target_idx] - pre_balances[target_idx]
            expected_lamports = int(expected_sol_amount * 1_000_000_000)
            
            # Allow tolerance of up to 0.0005 SOL (which covers standard discrepancies or tiny fees)
            if received_lamports > 0 and abs(received_lamports - expected_lamports) <= 500000:
                return True
                
    except Exception as e:
        print(f"Solana verification error: {e}")
        
    return False

def verify_usdt_trc20_transaction(tx_signature: str, target_address: str, expected_usdt_amount: float) -> bool:
    import urllib.request
    import json
    url = f"https://api.trongrid.io/v1/accounts/{target_address}/transactions/trc20?limit=20&only_confirmed=true"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode())
            transfers = res_data.get("data", [])
            
            expected_units = int(expected_usdt_amount * 1_000_000) # USDT has 6 decimals
            
            for tx in transfers:
                if tx.get("transaction_id") == tx_signature:
                    to_address = tx.get("to")
                    value_str = tx.get("value", "0")
                    value = int(value_str) if value_str.isdigit() else 0
                    symbol = tx.get("token_info", {}).get("symbol")
                    
                    if to_address == target_address and symbol == "USDT" and value >= expected_units:
                        return True
    except Exception as e:
        print(f"TRON verification error: {e}")
        
    return False

class PaymentCreateRequest(BaseModel):
    chips: int  # e.g., 10000, 50000, 100000
    currency: str  # 'SOL' or 'USDT'

@app.post("/api/crypto/create-payment")
def create_crypto_payment(req_data: PaymentCreateRequest, token: str = Query(...), db: Session = Depends(get_db)):
    user = get_current_user_from_token(token, db)
    
    # 10,000 chips = $10 USD
    usd_amount = (req_data.chips / 10000) * 10
    
    if req_data.currency.upper() == "USDT":
        crypto_amount = round(usd_amount, 2)
        deposit_address = USDT_WALLET_ADDRESS
    elif req_data.currency.upper() == "SOL":
        sol_price = get_sol_price()
        crypto_amount = round(usd_amount / sol_price, 4)
        deposit_address = SOL_WALLET_ADDRESS
    else:
        raise HTTPException(status_code=400, detail="Invalid cryptocurrency selection")
        
    payment_id = str(uuid.uuid4())
    
    # Generate QR Code URL using public server
    qr_data = f"{req_data.currency.lower()}:{deposit_address}?amount={crypto_amount}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&color=d4af37&bgcolor=121214&data={urllib.parse.quote(qr_data)}"
    
    PENDING_PAYMENTS[payment_id] = {
        "user_id": user.id,
        "chips": req_data.chips,
        "amount_crypto": crypto_amount,
        "currency": req_data.currency.upper(),
        "address": deposit_address,
        "created_at": datetime.utcnow()
    }
    
    return {
        "payment_id": payment_id,
        "chips": req_data.chips,
        "amount_crypto": crypto_amount,
        "currency": req_data.currency.upper(),
        "address": deposit_address,
        "qr_url": qr_url
    }

class PaymentVerifyRequest(BaseModel):
    payment_id: str
    tx_signature: str

@app.post("/api/crypto/verify-payment")
def verify_crypto_payment(req_data: PaymentVerifyRequest, token: str = Query(...), db: Session = Depends(get_db)):
    user = get_current_user_from_token(token, db)
    payment = PENDING_PAYMENTS.get(req_data.payment_id)
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment request not found or already verified")
        
    if payment["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized payment request")
        
    # Prevent double-spending by checking database for this signature
    clean_signature = req_data.tx_signature.strip()
    if not clean_signature:
        raise HTTPException(status_code=400, detail="Transaction signature/ID cannot be empty")
        
    existing_tx = db.query(ProcessedTransaction).filter(ProcessedTransaction.tx_signature == clean_signature).first()
    if existing_tx:
        raise HTTPException(status_code=400, detail="This transaction signature has already been processed.")
        
    # Perform on-chain validation
    success = False
    if payment["currency"] == "SOL":
        success = verify_solana_transaction(clean_signature, SOL_WALLET_ADDRESS, payment["amount_crypto"])
    elif payment["currency"] == "USDT":
        success = verify_usdt_trc20_transaction(clean_signature, USDT_WALLET_ADDRESS, payment["amount_crypto"])
        
    if not success:
        raise HTTPException(
            status_code=400, 
            detail="Transaction verification failed. Please make sure the transaction is confirmed, "
                   "sent the correct amount, and matches the correct recipient address."
        )
        
    # Credit chips
    user.chips += payment["chips"]
    
    # Save processed transaction
    processed_tx = ProcessedTransaction(
        tx_signature=clean_signature,
        currency=payment["currency"],
        amount_crypto=str(payment["amount_crypto"]),
        chips_credited=payment["chips"],
        user_id=user.id
    )
    db.add(processed_tx)
    
    db.commit()
    db.refresh(user)
    
    # Clean up pending payment
    PENDING_PAYMENTS.pop(req_data.payment_id, None)
    
    return {
        "status": "success",
        "message": f"Payment verified! Credited {payment['chips']:,} chips to your account.",
        "chips": user.chips
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
