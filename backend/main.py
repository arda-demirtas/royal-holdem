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

from models import Base, User, TournamentRecord, ProcessedTransaction, WithdrawalRequest
from poker_logic import PokerGame, Player

# Configurations
SECRET_KEY = "SUPER_SECRET_POKER_KEY_CHANGE_THIS"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 1 day
REQUIRED_PLAYERS = 4  # Set to 2 for testing. Revert to 4 for normal production.

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
    avatar_id: int
    games_played: int
    games_won: int
    hands_played: int
    hands_won: int
    win_rate: float
    hand_win_rate: float
    lp: int
    league_tier: int
    league_division: int

class WithdrawRequestSchema(BaseModel):
    chips: int
    currency: str
    address: str

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
    
    import random
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        chips=100000,  # Start chips
        avatar_id=random.randint(1, 8),
        lp=0,
        league_tier=1,
        league_division=3
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
        avatar_id=user.avatar_id,
        games_played=user.games_played,
        games_won=user.games_won,
        hands_played=user.hands_played,
        hands_won=user.hands_won,
        win_rate=user.win_rate,
        hand_win_rate=user.hand_win_rate,
        lp=user.lp,
        league_tier=user.league_tier,
        league_division=user.league_division
    )

@app.post("/api/claim-free-chips")
def claim_free_chips(token: str = Query(...), db: Session = Depends(get_db)):
    user = get_current_user_from_token(token, db)
    if user.chips < 1000:
        user.chips = 5000
        db.commit()
        return {"message": "Claimed 5,000 chips!", "chips": user.chips}
    raise HTTPException(status_code=400, detail="You must have less than 1,000 chips to claim free chips.")

class AvatarUpdateRequest(BaseModel):
    avatar_id: int

@app.post("/api/profile/update-avatar")
def update_profile_avatar(req_data: AvatarUpdateRequest, token: str = Query(...), db: Session = Depends(get_db)):
    user = get_current_user_from_token(token, db)
    if req_data.avatar_id < 1 or req_data.avatar_id > 8:
        raise HTTPException(status_code=400, detail="Invalid avatar ID. Must be between 1 and 8.")
    
    user.avatar_id = req_data.avatar_id
    db.commit()
    db.refresh(user)
    return {
        "status": "success",
        "message": "Avatar updated successfully.",
        "avatar_id": user.avatar_id
    }


# Lobby Matchmaking Logic
class Matchmaker:
    def __init__(self):
        # Maps connection (WebSocket) to user_id
        self.connections: Dict[WebSocket, int] = {}
        # Maps user_id to username
        self.user_names: Dict[int, str] = {}
        # Maps user_id to avatar_id
        self.user_avatars: Dict[int, int] = {}
        # Maps user_id to current bankroll chips
        self.user_chips: Dict[int, int] = {}
        # Maps user_id to league details
        self.user_lp: Dict[int, int] = {}
        self.user_tier: Dict[int, int] = {}
        self.user_division: Dict[int, int] = {}
        # Active queue
        self.queue: List[WebSocket] = []

    async def add(self, ws: WebSocket, user_id: int, username: str, avatar_id: int, chips: int, lp: int, tier: int, division: int):
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
        self.user_avatars[user_id] = avatar_id
        self.user_chips[user_id] = chips
        self.user_lp[user_id] = lp
        self.user_tier[user_id] = tier
        self.user_division[user_id] = division
        self.queue.append(ws)
        await self.broadcast_lobby_status()
        await self.check_match()

    def remove(self, ws: WebSocket):
        if ws in self.connections:
            user_id = self.connections.pop(ws)
            self.user_names.pop(user_id, None)
            self.user_avatars.pop(user_id, None)
            self.user_chips.pop(user_id, None)
            self.user_lp.pop(user_id, None)
            self.user_tier.pop(user_id, None)
            self.user_division.pop(user_id, None)
        if ws in self.queue:
            self.queue.remove(ws)
        asyncio.create_task(self.broadcast_lobby_status())

    async def broadcast_lobby_status(self):
        count = len(self.queue)
        users_list = [
            {
                "username": self.user_names[self.connections[ws]],
                "avatar_id": self.user_avatars[self.connections[ws]],
                "chips": self.user_chips[self.connections[ws]],
                "lp": self.user_lp[self.connections[ws]],
                "league_tier": self.user_tier[self.connections[ws]],
                "league_division": self.user_division[self.connections[ws]]
            }
            for ws in self.queue
        ]
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
        # We need exactly REQUIRED_PLAYERS players
        if len(self.queue) >= REQUIRED_PLAYERS:
            matched_ws = self.queue[:REQUIRED_PLAYERS]
            self.queue = self.queue[REQUIRED_PLAYERS:]

            matched_players = []
            for ws in matched_ws:
                uid = self.connections.pop(ws)
                uname = self.user_names.pop(uid)
                uavatar = self.user_avatars.pop(uid, 1)
                uchips = self.user_chips.pop(uid, 100000)
                ulp = self.user_lp.pop(uid, 0)
                utier = self.user_tier.pop(uid, 1)
                udiv = self.user_division.pop(uid, 3)
                matched_players.append((ws, uid, uname, uavatar, uchips, ulp, utier, udiv))

            # Deduct buy-in of 1,000 chips from each user database
            db = SessionLocal()
            valid_match = True
            for ws, uid, uname, uavatar, uchips, ulp, utier, udiv in matched_players:
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
                for ws, uid, uname, uavatar, uchips, ulp, utier, udiv in matched_players:
                    user = db.query(User).filter(User.id == uid).first()
                    if user and user.chips >= 1000:
                        await self.add(ws, uid, uname, uavatar, uchips, ulp, utier, udiv)
                return

            # Perform chips deduction & create tournament history
            tournament_id = str(uuid.uuid4())
            buy_in = 1000
            rake = 100  # 10% rake
            rake = 100  # 10% rake
            num_players = len(matched_players)
            prize_pool = (buy_in - rake) * num_players

            # Create tournament record
            tour_rec = TournamentRecord(
                id=tournament_id,
                buy_in=buy_in,
                rake=rake * num_players,
                prize_pool=prize_pool,
                winner_id=None
            )
            db.add(tour_rec)

            players_for_game = []
            for i, (ws, uid, uname, uavatar, uchips, ulp, utier, udiv) in enumerate(matched_players):
                user = db.query(User).filter(User.id == uid).first()
                user.chips -= buy_in
                user.games_played += 1
                players_for_game.append(Player(
                    user_id=uid, 
                    username=uname, 
                    chips=2000, 
                    seat_index=i, 
                    avatar_id=uavatar, 
                    bankroll_chips=user.chips,
                    lp=user.lp,
                    league_tier=user.league_tier,
                    league_division=user.league_division
                ))

            db.commit()
            db.close()

            # Create game
            game = PokerGame(tournament_id, players_for_game)
            ACTIVE_GAMES[tournament_id] = game
            game.start_game()

            # Notify all 4 matched players
            for ws, uid, uname, uavatar, uchips, ulp, utier, udiv in matched_players:
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
ACTIVE_VOICE_USERS: Dict[str, Set[int]] = {}

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
    avatar_id_val = user.avatar_id
    chips_val = user.chips
    lp_val = user.lp
    tier_val = user.league_tier
    div_val = user.league_division
    db.close()

    await matchmaker.add(websocket, user_id, username_val, avatar_id_val, chips_val, lp_val, tier_val, div_val)

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

def get_lp_change(tier: int, rank: int) -> int:
    if tier == 1:
        if rank == 1: return 25
        elif rank == 2: return -5
        elif rank == 3: return -10
        else: return -15
    elif tier == 2:
        if rank == 1: return 22
        elif rank == 2: return -7
        elif rank == 3: return -12
        else: return -18
    elif tier == 3:
        if rank == 1: return 20
        elif rank == 2: return -10
        elif rank == 3: return -15
        else: return -20
    elif tier == 4:
        if rank == 1: return 18
        elif rank == 2: return -12
        elif rank == 3: return -18
        else: return -22
    else:
        if rank == 1: return 15
        elif rank == 2: return -15
        elif rank == 3: return -20
        else: return -25

async def handle_disconnected_turns(tournament_id: str):
    """
    Auto-processes turns for disconnected players.
    """
    game = ACTIVE_GAMES.get(tournament_id)
    if not game or game.betting_round in ["showdown", "finished", "waiting"]:
        return

    # Loop to process actions for disconnected players whose turn it is
    while game.betting_round not in ["showdown", "finished", "waiting"]:
        active_player = game.players[game.current_turn_index]
        if not active_player.is_connected:
            action = "check" if active_player.current_bet == game.current_bet else "fold"
            game.log(f"[Auto] {active_player.username} is disconnected. Auto-acting: {action}")
            success = game.process_action(active_player.user_id, action)
            if success:
                if game.betting_round == "showdown":
                    asyncio.create_task(handle_game_continuation(tournament_id))
                    break
            else:
                break
        else:
            break

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
            # Award prize pool to winner
            tour_record = db.query(TournamentRecord).filter(TournamentRecord.id == tournament_id).first()
            awarded_chips = tour_record.prize_pool if tour_record else 3600
            winner_user = db.query(User).filter(User.id == winner_id).first()
            if winner_user:
                winner_user.chips += awarded_chips
                winner_user.games_won += 1
            
            # Update tournament record in db
            tour_record = db.query(TournamentRecord).filter(TournamentRecord.id == tournament_id).first()
            if tour_record:
                tour_record.winner_id = winner_id

            # Calculate rankings (1st to 4th)
            ranks = {winner_id: 1}
            elim_ids = game.eliminated_player_ids
            remaining_slots = [2, 3, 4]
            for uid in reversed(elim_ids):
                if uid not in ranks and remaining_slots:
                    ranks[uid] = remaining_slots.pop(0)
            
            # Fallback for any players not ranked
            for p in game.players:
                if p.user_id not in ranks:
                    if remaining_slots:
                        ranks[p.user_id] = remaining_slots.pop(0)
                    else:
                        ranks[p.user_id] = 4

            # Update LP, divisions, and tiers for each player
            for p in game.players:
                user = db.query(User).filter(User.id == p.user_id).first()
                if user:
                    player_rank = ranks.get(p.user_id, 4)
                    lp_change = get_lp_change(user.league_tier, player_rank)
                    user.lp += lp_change

                    # Promotion logic
                    if user.lp >= 100:
                        if user.league_tier == 5:
                            # Royal Sovereign: LP just grows, no limit
                            pass
                        else:
                            if user.league_division > 1:
                                user.league_division -= 1
                                user.lp = user.lp - 100
                            else:  # division == 1
                                user.league_tier += 1
                                if user.league_tier == 5:
                                    user.league_division = 0
                                else:
                                    user.league_division = 3
                                user.lp = user.lp - 100
                    
                    # Demotion logic
                    elif user.lp < 0:
                        if user.league_tier == 1 and user.league_division == 3:
                            user.lp = 0  # Bottom limit
                        else:
                            if user.league_tier == 5:
                                user.league_tier = 4
                                user.league_division = 1
                                user.lp = 100 + user.lp
                            else:
                                if user.league_division < 3:
                                    user.league_division += 1
                                    user.lp = 100 + user.lp
                                else:  # division == 3
                                    user.league_tier -= 1
                                    user.league_division = 1
                                    user.lp = 100 + user.lp

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
    await handle_disconnected_turns(tournament_id)
    await broadcast_game_state(tournament_id)

def get_websocket_for_user(tournament_id: str, user_id: int) -> Optional[WebSocket]:
    sockets = GAME_SOCKETS.get(tournament_id, set())
    for ws in sockets:
        details = SOCKET_TO_PLAYER.get(ws)
        if details and details[0] == tournament_id and details[1] == user_id:
            return ws
    return None

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
            # Handle chat message
            if data.get("type") == "chat":
                msg_text = data.get("message", "").strip()
                if msg_text:
                    sockets = GAME_SOCKETS.get(tournament_id, set())
                    for s in list(sockets):
                        try:
                            await s.send_json({
                                "type": "chat",
                                "username": username,
                                "message": msg_text[:150]
                            })
                        except Exception:
                            pass
                continue

            # Handle voice signalling events
            msg_type = data.get("type")
            if msg_type == "voice_joined":
                voice_users = ACTIVE_VOICE_USERS.setdefault(tournament_id, set())
                voice_users.add(user.id)
                
                # Send the list of current voice users back to the sender
                try:
                    await websocket.send_json({
                        "type": "voice_room_users",
                        "user_ids": list(voice_users)
                    })
                except Exception:
                    pass

                sockets = GAME_SOCKETS.get(tournament_id, set())
                for s in list(sockets):
                    if s != websocket:
                        try:
                            await s.send_json({
                                        "type": "player_voice_joined",
                                        "user_id": user.id
                                    })
                        except Exception:
                            pass
                continue

            elif msg_type == "voice_left":
                voice_users = ACTIVE_VOICE_USERS.get(tournament_id, set())
                if user.id in voice_users:
                    voice_users.remove(user.id)
                if not voice_users:
                    ACTIVE_VOICE_USERS.pop(tournament_id, None)

                sockets = GAME_SOCKETS.get(tournament_id, set())
                for s in list(sockets):
                    if s != websocket:
                        try:
                            await s.send_json({
                                        "type": "player_voice_left",
                                        "user_id": user.id
                                    })
                        except Exception:
                            pass
                continue

            elif msg_type == "voice_signal":
                target_id = data.get("target_id")
                signal = data.get("signal")
                if target_id is not None and signal is not None:
                    target_ws = get_websocket_for_user(tournament_id, target_id)
                    if target_ws:
                        try:
                            await target_ws.send_json({
                                        "type": "voice_signal",
                                        "sender_id": user.id,
                                        "signal": signal
                                    })
                        except Exception:
                            pass
                continue

            elif msg_type == "voice_state":
                is_speaking = data.get("is_speaking", False)
                sockets = GAME_SOCKETS.get(tournament_id, set())
                for s in list(sockets):
                    if s != websocket:
                        try:
                            await s.send_json({
                                        "type": "voice_state",
                                        "user_id": user.id,
                                        "is_speaking": is_speaking
                                    })
                        except Exception:
                            pass
                continue

            # Handle action
            action = data.get("action")  # 'fold', 'check', 'call', 'raise'
            amount = data.get("amount", 0)

            if action:
                success = game.process_action(user.id, action, amount)
                if success:
                    await handle_disconnected_turns(tournament_id)
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

        # Notify others they left voice
        voice_users = ACTIVE_VOICE_USERS.get(tournament_id, set())
        if user.id in voice_users:
            voice_users.remove(user.id)
        if not voice_users:
            ACTIVE_VOICE_USERS.pop(tournament_id, None)

        for s in list(sockets):
            try:
                await s.send_json({
                    "type": "player_voice_left",
                    "user_id": user.id
                })
            except Exception:
                pass

        # Handle auto turns if a disconnected player's turn is active
        await handle_disconnected_turns(tournament_id)
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

@app.get("/api/withdraw/estimate")
def estimate_withdrawal(chips: int = Query(...), currency: str = Query(...), token: str = Query(...), db: Session = Depends(get_db)):
    user = get_current_user_from_token(token, db)
    
    if chips < 10000:
        raise HTTPException(status_code=400, detail="Minimum withdrawal is 10,000 chips.")
        
    usd_amount = chips / 1000  # 1,000 chips = $1 USD
    
    if currency.upper() == "USDT":
        crypto_amount = round(usd_amount, 2)
        rate = 1.0
    elif currency.upper() == "SOL":
        sol_price = get_sol_price()
        crypto_amount = round(usd_amount / sol_price, 4)
        rate = sol_price
    else:
        raise HTTPException(status_code=400, detail="Invalid cryptocurrency selection.")
        
    return {
        "chips": chips,
        "currency": currency.upper(),
        "amount_crypto": crypto_amount,
        "rate": rate
    }

@app.post("/api/withdraw/create")
def create_withdrawal(req_data: WithdrawRequestSchema, token: str = Query(...), db: Session = Depends(get_db)):
    user = get_current_user_from_token(token, db)
    
    if req_data.chips < 10000:
        raise HTTPException(status_code=400, detail="Minimum withdrawal is 10,000 chips.")
        
    if user.chips < req_data.chips:
        raise HTTPException(status_code=400, detail="Insufficient chips balance.")
        
    address_clean = req_data.address.strip()
    if not address_clean:
        raise HTTPException(status_code=400, detail="Destination wallet address is required.")
        
    usd_amount = req_data.chips / 1000
    
    if req_data.currency.upper() == "USDT":
        crypto_amount = round(usd_amount, 2)
    elif req_data.currency.upper() == "SOL":
        sol_price = get_sol_price()
        crypto_amount = round(usd_amount / sol_price, 4)
    else:
        raise HTTPException(status_code=400, detail="Invalid cryptocurrency selection.")
        
    # Deduct chips immediately
    user.chips -= req_data.chips
    
    # Save withdrawal request
    new_request = WithdrawalRequest(
        user_id=user.id,
        amount_chips=req_data.chips,
        amount_crypto=str(crypto_amount),
        currency=req_data.currency.upper(),
        address=address_clean,
        status="pending"
    )
    db.add(new_request)
    db.commit()
    db.refresh(user)
    db.refresh(new_request)
    
    return {
        "status": "success",
        "message": "Withdrawal request submitted successfully!",
        "chips": user.chips,
        "request": {
            "id": new_request.id,
            "amount_chips": new_request.amount_chips,
            "amount_crypto": new_request.amount_crypto,
            "currency": new_request.currency,
            "address": new_request.address,
            "status": new_request.status,
            "created_at": new_request.created_at.isoformat()
        }
    }

@app.get("/api/withdraw/history")
def get_withdrawal_history(token: str = Query(...), db: Session = Depends(get_db)):
    user = get_current_user_from_token(token, db)
    requests = db.query(WithdrawalRequest).filter(WithdrawalRequest.user_id == user.id).order_by(WithdrawalRequest.created_at.desc()).all()
    
    return [
        {
            "id": r.id,
            "amount_chips": r.amount_chips,
            "amount_crypto": r.amount_crypto,
            "currency": r.currency,
            "address": r.address,
            "status": r.status,
            "created_at": r.created_at.isoformat()
        }
        for r in requests
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
