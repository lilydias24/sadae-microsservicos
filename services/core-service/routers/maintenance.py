from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from database_models import ServiceOrder, Maintenance, Complaint

router = APIRouter()

@router.get("/orders")
async def get_orders(db: Session = Depends(get_db)):
    """Get service orders"""
    orders = db.query(ServiceOrder).all()
    return orders

@router.post("/orders")
async def create_order(order_data: dict, db: Session = Depends(get_db)):
    """Create service order"""
    order = ServiceOrder(**order_data)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@router.post("/public/complaints")
async def create_complaint(complaint_data: dict, db: Session = Depends(get_db)):
    """Create public complaint"""
    complaint = Complaint(**complaint_data)
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint