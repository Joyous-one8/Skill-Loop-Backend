from typing import Generator
from fastapi import Depends, HTTPException, status, Security
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import auth
from app.models.database import User


async def get_current_user(
    db: Session = Depends(get_db),
    token_payload: dict = Security(auth.verify)
) -> User:
    auth0_id = token_payload.get("sub")
    
    if not auth0_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user
