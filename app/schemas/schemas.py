from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from app.models.database import SkillLevel, SkillType, MatchStatus, SessionStatus, SessionType


class UserBase(BaseModel):
    email: EmailStr
    name: str
    bio: Optional[str] = None
    avatar: Optional[str] = None
    availability: Optional[List] = None


class UserCreate(UserBase):
    auth0_id: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None
    availability: Optional[List] = None


class UserResponse(UserBase):
    id: UUID
    credits: int
    rating: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SkillBase(BaseModel):
    name: str
    level: SkillLevel
    category: str
    priority: int = 0
    type: SkillType


class SkillCreate(SkillBase):
    pass


class SkillResponse(SkillBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class MatchBase(BaseModel):
    matched_user_id: UUID
    match_score: float = Field(..., ge=0, le=100)
    common_skills: List[str]


class MatchCreate(MatchBase):
    pass


class MatchResponse(MatchBase):
    id: UUID
    user_id: UUID
    status: MatchStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SessionBase(BaseModel):
    title: str
    participant_id: UUID
    participant_name: str
    skill: str
    date: str
    time: str
    duration: int
    type: SessionType


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    title: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    duration: Optional[int] = None
    status: Optional[SessionStatus] = None


class SessionRatingRequest(BaseModel):
    rating: float = Field(..., ge=0.0, le=5.0)
    feedback: Optional[str] = None


class SessionResponse(SessionBase):
    id: UUID
    user_id: UUID
    status: SessionStatus
    rating: Optional[float] = None
    feedback: Optional[str] = None
    rated_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CreditTransactionBase(BaseModel):
    amount: int
    transaction_type: str
    description: Optional[str] = None


class CreditTransactionCreate(CreditTransactionBase):
    session_id: Optional[UUID] = None


class CreditTransactionResponse(CreditTransactionBase):
    id: UUID
    user_id: UUID
    session_id: Optional[UUID] = None
    balance_after: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CreditBalanceResponse(BaseModel):
    user_id: UUID
    credits: int
