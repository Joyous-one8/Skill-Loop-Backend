from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.database import User, Session as DBSession, SessionStatus, CreditTransaction
from app.schemas.schemas import SessionResponse, SessionCreate, SessionUpdate, SessionRatingRequest

router = APIRouter()


@router.get("/", response_model=List[SessionResponse])
async def get_user_sessions(
    status_filter: SessionStatus = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(DBSession).filter(
        or_(
            DBSession.user_id == current_user.id,
            DBSession.participant_id == current_user.id
        )
    )
    
    if status_filter:
        query = query.filter(DBSession.status == status_filter)
    
    sessions = query.order_by(DBSession.created_at.desc()).all()
    return sessions


@router.get("/history", response_model=List[SessionResponse])
async def get_session_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = db.query(DBSession).filter(
        and_(
            or_(
                DBSession.user_id == current_user.id,
                DBSession.participant_id == current_user.id
            ),
            DBSession.status == SessionStatus.completed
        )
    ).order_by(DBSession.updated_at.desc()).all()
    
    return sessions


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_session = DBSession(**session_data.dict(), user_id=current_user.id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: UUID,
    session_update: SessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(DBSession).filter(
        DBSession.id == session_id,
        DBSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    for field, value in session_update.dict(exclude_unset=True).items():
        setattr(session, field, value)
    
    db.commit()
    db.refresh(session)
    return session


@router.post("/{session_id}/complete", response_model=SessionResponse)
async def complete_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(DBSession).filter(
        DBSession.id == session_id,
        or_(
            DBSession.user_id == current_user.id,
            DBSession.participant_id == current_user.id
        )
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.status != SessionStatus.scheduled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only complete scheduled sessions"
        )
    
    session.status = SessionStatus.completed
    
    # Award credits to the teacher
    if session.type.value == "teaching":
        teacher = db.query(User).filter(User.id == session.user_id).first()
        if teacher:
            credits_earned = session.duration // 15  # 1 credit per 15 minutes
            teacher.credits += credits_earned
            
            # Create credit transaction
            transaction = CreditTransaction(
                user_id=teacher.id,
                session_id=session.id,
                amount=credits_earned,
                transaction_type="earned",
                description=f"Earned from teaching session: {session.title}",
                balance_after=teacher.credits
            )
            db.add(transaction)
    
    db.commit()
    db.refresh(session)
    return session


@router.post("/{session_id}/rate", response_model=SessionResponse)
async def rate_session(
    session_id: UUID,
    rating_data: SessionRatingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(DBSession).filter(
        DBSession.id == session_id,
        or_(
            DBSession.user_id == current_user.id,
            DBSession.participant_id == current_user.id
        )
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.status != SessionStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only rate completed sessions"
        )
    
    if session.rating is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session already rated"
        )
    
    # Update session rating
    session.rating = rating_data.rating
    session.feedback = rating_data.feedback
    session.rated_by = current_user.id
    
    # Update the rated user's overall rating
    rated_user_id = session.participant_id if session.user_id == current_user.id else session.user_id
    rated_user = db.query(User).filter(User.id == rated_user_id).first()
    
    if rated_user:
        # Get all ratings for this user
        all_sessions_as_participant = db.query(DBSession).filter(
            and_(
                DBSession.participant_id == rated_user_id,
                DBSession.rating.isnot(None)
            )
        ).all()
        
        all_sessions_as_organizer = db.query(DBSession).filter(
            and_(
                DBSession.user_id == rated_user_id,
                DBSession.rating.isnot(None)
            )
        ).all()
        
        all_ratings = [s.rating for s in all_sessions_as_participant + all_sessions_as_organizer]
        
        if all_ratings:
            rated_user.rating = sum(all_ratings) / len(all_ratings)
    
    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(DBSession).filter(
        DBSession.id == session_id,
        DBSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    db.delete(session)
    db.commit()
    return None
