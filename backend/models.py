from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    chips = Column(Integer, default=100000)  # Starting bankroll
    avatar_id = Column(Integer, default=1)
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    hands_played = Column(Integer, default=0)
    hands_won = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to Tournaments won
    tournaments_won = relationship("TournamentRecord", back_populates="winner")

    @property
    def win_rate(self) -> float:
        if self.games_played == 0:
            return 0.0
        return round((self.games_won / self.games_played) * 100, 1)

    @property
    def hand_win_rate(self) -> float:
        if self.hands_played == 0:
            return 0.0
        return round((self.hands_won / self.hands_played) * 100, 1)

class TournamentRecord(Base):
    __tablename__ = "tournament_records"

    id = Column(String, primary_key=True, index=True)
    buy_in = Column(Integer, nullable=False)
    rake = Column(Integer, nullable=False)
    prize_pool = Column(Integer, nullable=False)
    winner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    winner = relationship("User", back_populates="tournaments_won")

class ProcessedTransaction(Base):
    __tablename__ = "processed_transactions"

    id = Column(Integer, primary_key=True, index=True)
    tx_signature = Column(String, unique=True, index=True, nullable=False)
    currency = Column(String, nullable=False)
    amount_crypto = Column(String, nullable=False)
    chips_credited = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="processed_transactions")

