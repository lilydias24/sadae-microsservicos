"""
Support Engine - Business Logic
Handles support business rules and calculations
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

class TicketPriorityCalculator:
    """Calculate ticket priority based on various factors"""
    
    @staticmethod
    def calculate_priority(
        category: str,
        client_tier: str = "standard",
        related_bill_amount: float = 0.0,
        is_emergency: bool = False,
        client_satisfaction_history: float = 5.0
    ) -> str:
        """Calculate ticket priority based on multiple factors"""
        
        if is_emergency:
            return "urgent"
        
        priority_score = 0
        
        # Category weight
        category_weights = {
            "billing": 3,
            "technical": 4,
            "complaint": 2,
            "request": 1,
            "information": 1,
            "emergency": 5
        }
        priority_score += category_weights.get(category, 1)
        
        # Client tier weight
        tier_weights = {
            "premium": 3,
            "standard": 2,
            "basic": 1
        }
        priority_score += tier_weights.get(client_tier, 2)
        
        # Bill amount influence
        if related_bill_amount > 1000:
            priority_score += 2
        elif related_bill_amount > 500:
            priority_score += 1
        
        # Client satisfaction influence
        if client_satisfaction_history < 3.0:
            priority_score += 2
        elif client_satisfaction_history < 4.0:
            priority_score += 1
        
        # Convert score to priority
        if priority_score >= 8:
            return "urgent"
        elif priority_score >= 6:
            return "high"
        elif priority_score >= 4:
            return "medium"
        else:
            return "low"

class SLACalculator:
    """Calculate SLA compliance and deadlines"""
    
    SLA_TIMES = {
        "urgent": {"response": 1, "resolution": 4},      # hours
        "high": {"response": 2, "resolution": 8},
        "medium": {"response": 4, "resolution": 24},
        "low": {"response": 8, "resolution": 72}
    }
    
    @classmethod
    def calculate_deadlines(cls, priority: str, created_at: datetime) -> Dict[str, datetime]:
        """Calculate SLA deadlines for a ticket"""
        sla = cls.SLA_TIMES.get(priority, cls.SLA_TIMES["medium"])
        
        response_deadline = created_at + timedelta(hours=sla["response"])
        resolution_deadline = created_at + timedelta(hours=sla["resolution"])
        
        return {
            "response_deadline": response_deadline,
            "resolution_deadline": resolution_deadline
        }
    
    @classmethod
    def check_sla_compliance(
        cls, 
        priority: str, 
        created_at: datetime,
        first_response_at: Optional[datetime] = None,
        resolved_at: Optional[datetime] = None
    ) -> Dict[str, bool]:
        """Check if ticket is compliant with SLA"""
        deadlines = cls.calculate_deadlines(priority, created_at)
        
        response_compliant = True
        resolution_compliant = True
        
        if first_response_at:
            response_compliant = first_response_at <= deadlines["response_deadline"]
        else:
            # Check if still within response time
            response_compliant = datetime.now() <= deadlines["response_deadline"]
        
        if resolved_at:
            resolution_compliant = resolved_at <= deadlines["resolution_deadline"]
        else:
            # Check if still within resolution time
            resolution_compliant = datetime.now() <= deadlines["resolution_deadline"]
        
        return {
            "response_compliant": response_compliant,
            "resolution_compliant": resolution_compliant,
            "response_overdue": not response_compliant and not first_response_at,
            "resolution_overdue": not resolution_compliant and not resolved_at
        }

class AutoAssignmentEngine:
    """Automatic ticket assignment based on workload and expertise"""
    
    @staticmethod
    def calculate_agent_score(
        agent: Dict[str, Any],
        ticket_category: str,
        current_workload: int
    ) -> float:
        """Calculate agent score for ticket assignment"""
        score = 0.0
        
        # Expertise in category
        expertise = agent.get("expertise", {})
        category_expertise = expertise.get(ticket_category, 0.5)
        score += category_expertise * 40  # 40% weight
        
        # Workload (inverse relationship)
        max_tickets = agent.get("max_concurrent_tickets", 10)
        workload_factor = max(0, (max_tickets - current_workload) / max_tickets)
        score += workload_factor * 30  # 30% weight
        
        # Agent availability
        if agent.get("is_available", True):
            score += 20  # 20% weight
        
        # Agent performance metrics
        satisfaction_rating = agent.get("satisfaction_average", 5.0)
        score += (satisfaction_rating / 5.0) * 10  # 10% weight
        
        return score
    
    @staticmethod
    def find_best_agent(
        available_agents: List[Dict[str, Any]],
        ticket_category: str,
        agent_workloads: Dict[int, int]
    ) -> Optional[Dict[str, Any]]:
        """Find the best agent for ticket assignment"""
        if not available_agents:
            return None
        
        best_agent = None
        best_score = -1
        
        for agent in available_agents:
            current_workload = agent_workloads.get(agent["user_id"], 0)
            score = AutoAssignmentEngine.calculate_agent_score(
                agent, ticket_category, current_workload
            )
            
            if score > best_score:
                best_score = score
                best_agent = agent
        
        return best_agent

class EscalationEngine:
    """Handle ticket escalation logic"""
    
    ESCALATION_RULES = {
        "time_based": {
            "urgent": 2,    # hours
            "high": 4,
            "medium": 8,
            "low": 24
        },
        "satisfaction_threshold": 3.0,
        "unresolved_messages": 5
    }
    
    @classmethod
    def should_escalate(
        cls,
        ticket: Dict[str, Any],
        messages_count: int,
        last_agent_response: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Determine if ticket should be escalated"""
        reasons = []
        escalate = False
        
        priority = ticket.get("priority", "medium")
        created_at = ticket.get("created_at")
        
        # Time-based escalation
        if created_at and priority in cls.ESCALATION_RULES["time_based"]:
            escalation_time = cls.ESCALATION_RULES["time_based"][priority]
            if datetime.now() > created_at + timedelta(hours=escalation_time):
                reasons.append(f"Ticket não resolvido em {escalation_time} horas")
                escalate = True
        
        # Agent inactivity
        if last_agent_response:
            inactive_hours = (datetime.now() - last_agent_response).total_seconds() / 3600
            if inactive_hours > 4:  # 4 hours of inactivity
                reasons.append(f"Agente inativo há {inactive_hours:.1f} horas")
                escalate = True
        
        # Too many client messages without resolution
        if messages_count > cls.ESCALATION_RULES["unresolved_messages"]:
            reasons.append(f"Muitas mensagens sem resolução ({messages_count})")
            escalate = True
        
        # Low satisfaction
        satisfaction = ticket.get("satisfaction_rating")
        if satisfaction and satisfaction < cls.ESCALATION_RULES["satisfaction_threshold"]:
            reasons.append(f"Baixa satisfação do cliente ({satisfaction})")
            escalate = True
        
        return {
            "should_escalate": escalate,
            "reasons": reasons,
            "escalation_level": cls._determine_escalation_level(ticket, reasons)
        }
    
    @classmethod
    def _determine_escalation_level(cls, ticket: Dict[str, Any], reasons: List[str]) -> str:
        """Determine the level of escalation needed"""
        priority = ticket.get("priority", "medium")
        reason_count = len(reasons)
        
        if priority == "urgent" or reason_count >= 3:
            return "manager"
        elif priority == "high" or reason_count >= 2:
            return "supervisor"
        else:
            return "senior_agent"

class KnowledgeBaseMatcher:
    """Match tickets with relevant knowledge base articles"""
    
    @staticmethod
    def find_relevant_articles(
        ticket_title: str,
        ticket_description: str,
        ticket_category: str,
        articles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find knowledge base articles relevant to the ticket"""
        relevant_articles = []
        
        # Simple keyword matching (in production, use more sophisticated NLP)
        ticket_text = f"{ticket_title} {ticket_description}".lower()
        
        for article in articles:
            score = 0
            
            # Category match
            if article.get("category") == ticket_category:
                score += 30
            
            # Title keywords
            title_words = article.get("title", "").lower().split()
            for word in title_words:
                if word in ticket_text and len(word) > 3:
                    score += 10
            
            # Content keywords
            content_words = article.get("content", "").lower().split()[:50]  # First 50 words
            for word in content_words:
                if word in ticket_text and len(word) > 3:
                    score += 5
            
            # Tags match
            tags = article.get("tags", "").lower()
            if tags:
                tag_list = tags.split(",")
                for tag in tag_list:
                    if tag.strip() in ticket_text:
                        score += 15
            
            if score > 20:  # Minimum relevance threshold
                relevant_articles.append({
                    "article": article,
                    "relevance_score": score
                })
        
        # Sort by relevance and return top 5
        relevant_articles.sort(key=lambda x: x["relevance_score"], reverse=True)
        return relevant_articles[:5]

class SupportMetricsCalculator:
    """Calculate various support metrics"""
    
    @staticmethod
    def calculate_agent_performance(
        agent_tickets: List[Dict[str, Any]],
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """Calculate agent performance metrics"""
        if not agent_tickets:
            return {
                "tickets_resolved": 0,
                "average_resolution_time": 0,
                "satisfaction_average": 0,
                "response_time_average": 0,
                "escalation_rate": 0
            }
        
        resolved_tickets = [t for t in agent_tickets if t.get("resolved_at")]
        total_satisfaction = sum(t.get("satisfaction_rating", 0) for t in agent_tickets if t.get("satisfaction_rating"))
        satisfaction_count = len([t for t in agent_tickets if t.get("satisfaction_rating")])
        
        # Calculate averages
        avg_resolution_time = 0
        if resolved_tickets:
            resolution_times = []
            for ticket in resolved_tickets:
                created = ticket.get("created_at")
                resolved = ticket.get("resolved_at")
                if created and resolved:
                    time_diff = (resolved - created).total_seconds() / 3600  # hours
                    resolution_times.append(time_diff)
            
            if resolution_times:
                avg_resolution_time = sum(resolution_times) / len(resolution_times)
        
        # Escalation rate
        escalated_tickets = len([t for t in agent_tickets if t.get("escalated", False)])
        escalation_rate = (escalated_tickets / len(agent_tickets)) * 100 if agent_tickets else 0
        
        return {
            "tickets_resolved": len(resolved_tickets),
            "average_resolution_time": round(avg_resolution_time, 2),
            "satisfaction_average": round(total_satisfaction / satisfaction_count, 2) if satisfaction_count > 0 else 0,
            "escalation_rate": round(escalation_rate, 2),
            "total_tickets_handled": len(agent_tickets)
        }
    
    @staticmethod
    def calculate_team_metrics(
        all_tickets: List[Dict[str, Any]],
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """Calculate team-wide support metrics"""
        if not all_tickets:
            return {}
        
        # Filter tickets by time period
        cutoff_date = datetime.now() - timedelta(days=time_period_days)
        recent_tickets = [t for t in all_tickets if t.get("created_at", datetime.min) >= cutoff_date]
        
        # Category distribution
        category_counts = {}
        for ticket in recent_tickets:
            category = ticket.get("category", "unknown")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Priority distribution
        priority_counts = {}
        for ticket in recent_tickets:
            priority = ticket.get("priority", "medium")
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Resolution rate
        resolved_count = len([t for t in recent_tickets if t.get("resolved_at")])
        resolution_rate = (resolved_count / len(recent_tickets)) * 100 if recent_tickets else 0
        
        # Average satisfaction
        satisfaction_ratings = [t.get("satisfaction_rating") for t in recent_tickets if t.get("satisfaction_rating")]
        avg_satisfaction = sum(satisfaction_ratings) / len(satisfaction_ratings) if satisfaction_ratings else 0
        
        return {
            "total_tickets": len(recent_tickets),
            "resolution_rate": round(resolution_rate, 2),
            "average_satisfaction": round(avg_satisfaction, 2),
            "category_distribution": category_counts,
            "priority_distribution": priority_counts,
            "time_period_days": time_period_days
        }

@dataclass
class TicketWorkflow:
    """Define ticket workflow states and transitions"""
    
    VALID_TRANSITIONS = {
        "open": ["in_progress", "closed"],
        "in_progress": ["waiting_client", "resolved", "escalated", "closed"],
        "waiting_client": ["in_progress", "closed"],
        "escalated": ["in_progress", "resolved", "closed"],
        "resolved": ["closed", "reopened"],
        "closed": ["reopened"],
        "reopened": ["in_progress", "closed"]
    }
    
    @classmethod
    def can_transition(cls, current_status: str, new_status: str) -> bool:
        """Check if status transition is valid"""
        allowed_transitions = cls.VALID_TRANSITIONS.get(current_status, [])
        return new_status in allowed_transitions
    
    @classmethod
    def get_available_transitions(cls, current_status: str) -> List[str]:
        """Get list of available status transitions"""
        return cls.VALID_TRANSITIONS.get(current_status, [])