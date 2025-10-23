from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.database import User, CreditTransaction
from app.schemas.schemas import CreditTransactionResponse, CreditTransactionCreate, CreditBalanceResponse

router = APIRouter()


@router.get("/balance", response_model=CreditBalanceResponse)
async def get_credit_balance(
    current_user: User = Depends(get_current_user)
):
    return CreditBalanceResponse(
        user_id=current_user.id,
        credits=current_user.credits
    )


@router.get("/history", response_model=List[CreditTransactionResponse])
async def get_credit_history(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transactions = db.query(CreditTransaction).filter(
        CreditTransaction.user_id == current_user.id
    ).order_by(desc(CreditTransaction.created_at)).offset(skip).limit(limit).all()
    
    return transactions


@router.post("/earn", response_model=CreditTransactionResponse, status_code=status.HTTP_201_CREATED)
async def earn_credits(
    transaction_data: CreditTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if transaction_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive for earning credits"
        )
    
    current_user.credits += transaction_data.amount
    balance_after = current_user.credits
    
    transaction = CreditTransaction(
        user_id=current_user.id,
        session_id=transaction_data.session_id,
        amount=transaction_data.amount,
        transaction_type=transaction_data.transaction_type,
        description=transaction_data.description,
        balance_after=balance_after
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return transaction


@router.post("/spend", response_model=CreditTransactionResponse)
async def spend_credits(
    transaction_data: CreditTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    amount = abs(transaction_data.amount)
    
    if current_user.credits < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient credits. You have {current_user.credits} credits but need {amount}"
        )
    
    current_user.credits -= amount
    balance_after = current_user.credits
    
    transaction = CreditTransaction(
        user_id=current_user.id,
        session_id=transaction_data.session_id,
        amount=-amount,
        transaction_type="spent",
        description=transaction_data.description,
        balance_after=balance_after
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return transaction


@router.get("/transactions/{transaction_id}", response_model=CreditTransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transaction = db.query(CreditTransaction).filter(
        CreditTransaction.id == transaction_id,
        CreditTransaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return transaction
