from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.database import User, Match, MatchStatus
from app.schemas.schemas import MatchResponse, MatchCreate

router = APIRouter()


@router.get("/", response_model=List[MatchResponse])
async def get_user_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    matches = db.query(Match).filter(Match.user_id == current_user.id).all()
    return matches


@router.post("/", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
async def create_match(
    match_data: MatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_match = Match(**match_data.dict(), user_id=current_user.id)
    db.add(new_match)
    db.commit()
    db.refresh(new_match)
    return new_match


@router.post("/{match_id}/accept", response_model=MatchResponse)
async def accept_match(
    match_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    match = db.query(Match).filter(
        Match.id == match_id,
        Match.user_id == current_user.id
    ).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    match.status = MatchStatus.accepted
    db.commit()
    db.refresh(match)
    return match


@router.post("/{match_id}/reject", response_model=MatchResponse)
async def reject_match(
    match_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    match = db.query(Match).filter(
        Match.id == match_id,
        Match.user_id == current_user.id
    ).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    match.status = MatchStatus.rejected
    db.commit()
    db.refresh(match)
    return match
