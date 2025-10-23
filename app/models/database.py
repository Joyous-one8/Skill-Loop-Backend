import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, ForeignKey, JSON, Text, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class SkillLevel(enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class SkillType(enum.Enum):
    teaching = "teaching"
    learning = "learning"


class MatchStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class SessionStatus(enum.Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"


class SessionType(enum.Enum):
    teaching = "teaching"
    learning = "learning"


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    auth0_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    bio = Column(Text, nullable=True)
    avatar = Column(String(500), nullable=True)
    availability = Column(JSON, nullable=True)
    credits = Column(Integer, default=0)
    rating = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    skills = relationship("Skill", back_populates="user", cascade="all, delete-orphan")
    sessions_organized = relationship("Session", foreign_keys="Session.user_id", back_populates="organizer")
    sessions_participated = relationship("Session", foreign_keys="Session.participant_id", back_populates="participant")
    matches_received = relationship("Match", foreign_keys="Match.user_id", back_populates="user")
    matches_given = relationship("Match", foreign_keys="Match.matched_user_id", back_populates="matched_user")
    credit_transactions = relationship("CreditTransaction", back_populates="user", cascade="all, delete-orphan")


class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    level = Column(Enum(SkillLevel), nullable=False)
    category = Column(String(100), nullable=False)
    priority = Column(Integer, default=0)
    type = Column(Enum(SkillType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="skills")
    
    __table_args__ = (
        Index('ix_skills_user_id', 'user_id'),
        Index('ix_skills_category', 'category'),
        Index('ix_skills_user_type', 'user_id', 'type'),
    )


class Match(Base):
    __tablename__ = "matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    matched_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    match_score = Column(Float, nullable=False)
    common_skills = Column(JSON, nullable=False)
    status = Column(Enum(MatchStatus), default=MatchStatus.pending, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", foreign_keys=[user_id], back_populates="matches_received")
    matched_user = relationship("User", foreign_keys=[matched_user_id], back_populates="matches_given")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'matched_user_id', name='uq_match_users'),
        CheckConstraint('user_id != matched_user_id', name='ck_match_different_users'),
        CheckConstraint('match_score >= 0 AND match_score <= 100', name='ck_match_score_range'),
    )


class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    participant_name = Column(String(255), nullable=False)
    skill = Column(String(100), nullable=False)
    date = Column(String(50), nullable=False)
    time = Column(String(10), nullable=False)
    duration = Column(Integer, nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.scheduled, nullable=False)
    type = Column(Enum(SessionType), nullable=False)
    
    # Rating fields
    rating = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    rated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organizer = relationship("User", foreign_keys=[user_id], back_populates="sessions_organized")
    participant = relationship("User", foreign_keys=[participant_id], back_populates="sessions_participated")
    rater = relationship("User", foreign_keys=[rated_by])
    
    __table_args__ = (
        Index('ix_sessions_user_id', 'user_id'),
        Index('ix_sessions_date', 'date'),
        Index('ix_sessions_status', 'status'),
        CheckConstraint('rating IS NULL OR (rating >= 0 AND rating <= 5)', name='ck_rating_range'),
    )


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Integer, nullable=False)
    transaction_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    balance_after = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="credit_transactions")
    session = relationship("Session")
    
    __table_args__ = (
        Index('ix_credit_transactions_user_id', 'user_id'),
        Index('ix_credit_transactions_created_at', 'created_at'),
    )
