from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from database_models import SupportTicket, TicketMessage, KnowledgeBaseArticle, SupportAgent

router = APIRouter()

@router.get("/tickets")
async def get_tickets(db: Session = Depends(get_db)):
    """Get all support tickets"""
    tickets = db.query(SupportTicket).all()
    return tickets

@router.post("/tickets")
async def create_ticket(ticket_data: dict, db: Session = Depends(get_db)):
    """Create support ticket"""
    ticket = SupportTicket(**ticket_data)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Get specific ticket"""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@router.put("/tickets/{ticket_id}")
async def update_ticket(ticket_id: int, ticket_data: dict, db: Session = Depends(get_db)):
    """Update ticket"""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    for key, value in ticket_data.items():
        setattr(ticket, key, value)
    
    db.commit()
    return ticket

@router.get("/knowledge-base")
async def get_knowledge_base(category: str = None, db: Session = Depends(get_db)):
    """Get knowledge base articles"""
    query = db.query(KnowledgeBaseArticle)
    if category:
        query = query.filter(KnowledgeBaseArticle.category == category)
    return query.all()

@router.get("/dashboard")
async def get_dashboard(db: Session = Depends(get_db)):
    """Get support dashboard"""
    total_tickets = db.query(SupportTicket).count()
    open_tickets = db.query(SupportTicket).filter(SupportTicket.status == "open").count()
    return {"total_tickets": total_tickets, "open_tickets": open_tickets}