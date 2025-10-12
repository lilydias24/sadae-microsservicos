from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from database_models import Customer, Bill, Payment, BillContest, DebtNegotiation

router = APIRouter()

@router.get("/bills")
async def get_bills(db: Session = Depends(get_db)):
    """Get all bills"""
    bills = db.query(Bill).all()
    return bills

@router.post("/contests")
async def create_contest(contest_data: dict, db: Session = Depends(get_db)):
    """Create bill contest"""
    contest = BillContest(**contest_data)
    db.add(contest)
    db.commit()
    db.refresh(contest)
    return contest

@router.get("/contests")
async def get_contests(db: Session = Depends(get_db)):
    """Get all contests"""
    contests = db.query(BillContest).all()
    return contests

@router.put("/contests/{contest_id}/resolve")
async def resolve_contest(contest_id: int, resolution: str, approved: bool, db: Session = Depends(get_db)):
    """Resolve contest"""
    contest = db.query(BillContest).filter(BillContest.id == contest_id).first()
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    
    contest.resolution = resolution
    contest.status = "approved" if approved else "rejected"
    db.commit()
    return contest

@router.post("/negotiations")
async def create_negotiation(negotiation_data: dict, db: Session = Depends(get_db)):
    """Create debt negotiation"""
    negotiation = DebtNegotiation(**negotiation_data)
    db.add(negotiation)
    db.commit()
    db.refresh(negotiation)
    return negotiation

@router.get("/negotiations")
async def get_negotiations(db: Session = Depends(get_db)):
    """Get all negotiations"""
    negotiations = db.query(DebtNegotiation).all()
    return negotiations

@router.post("/payments")
async def process_payment(payment_data: dict, db: Session = Depends(get_db)):
    """Process payment"""
    payment = Payment(**payment_data)
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment