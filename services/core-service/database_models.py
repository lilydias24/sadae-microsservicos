from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
Base = declarative_base()

# Definir enums necessários
class BillStatus:
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class ServiceOrderStatus:
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class AnomalyStatus:
    PENDING = "pending"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_ALARM = "false_alarm"


# Billing Models
class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True)  # Reference to auth service user
    name = Column(String, nullable=False)
    document = Column(String, unique=True, nullable=False)  # CPF/CNPJ
    email = Column(String, nullable=False)
    phone = Column(String)
    address = Column(Text, nullable=False)
    customer_type = Column(String, default="residential")  # residential, commercial, industrial
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WaterMeter(Base):
    __tablename__ = "water_meters"
    
    id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(String, unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    location = Column(String, nullable=False)
    installation_date = Column(DateTime, nullable=False)
    last_reading = Column(Float, default=0.0)
    last_reading_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class MeterReading(Base):
    __tablename__ = "meter_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(String, ForeignKey("water_meters.meter_id"), nullable=False)
    reading_value = Column(Float, nullable=False)
    reading_date = Column(DateTime, nullable=False)
    consumption = Column(Float)  # Calculated consumption since last reading
    created_at = Column(DateTime, default=datetime.utcnow)

class Bill(Base):
    __tablename__ = "bills"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    meter_id = Column(String, ForeignKey("water_meters.meter_id"))
    amount = Column(Numeric(10, 2), nullable=False)
    consumption = Column(Float, nullable=False)
    billing_period_start = Column(DateTime, nullable=False)
    billing_period_end = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(String, default=BillStatus.PENDING)
    paid_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class BillContest(Base):
    __tablename__ = "bill_contests"
    
    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False)
    protocol_number = Column(String, unique=True, nullable=False)
    reason = Column(Text, nullable=False)
    description = Column(Text)
    status = Column(String, default="pending")  # pending, approved, rejected
    resolution = Column(Text)
    resolved_at = Column(DateTime)
    resolved_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class DebtNegotiation(Base):
    __tablename__ = "debt_negotiations"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    total_debt = Column(Numeric(10, 2), nullable=False)
    installments = Column(Integer, nullable=False)
    installment_amount = Column(Numeric(10, 2), nullable=False)
    discount_percentage = Column(Float, default=0.0)
    interest_rate = Column(Float, default=0.0)
    status = Column(String, default="proposed")  # proposed, active, completed, cancelled
    start_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String, nullable=False)  # credit_card, debit_card, bank_transfer, cash
    payment_date = Column(DateTime, default=datetime.utcnow)
    transaction_id = Column(String)
    status = Column(String, default="completed")  # pending, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)

class TariffRate(Base):
    __tablename__ = "tariff_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_type = Column(String, nullable=False)  # residential, commercial, industrial
    tier_start = Column(Float, nullable=False)  # m³ start range
    tier_end = Column(Float)  # m³ end range (null for unlimited)
    rate_per_m3 = Column(Numeric(10, 4), nullable=False)
    fixed_charge = Column(Numeric(10, 2), default=0.0)
    effective_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Support Models  
class SupportTicket(Base):
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(30), unique=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # billing, technical, complaint, request, information, emergency
    priority = Column(String(20), nullable=False, default="medium")  # low, medium, high, urgent
    status = Column(String(30), nullable=False, default="open")  # open, in_progress, waiting_client, resolved, closed, forwarded
    client_id = Column(Integer, nullable=False)
    client_name = Column(String(100), nullable=False)
    client_email = Column(String(100), nullable=False)
    client_phone = Column(String(20), nullable=True)
    assigned_agent_id = Column(Integer, nullable=True)
    assigned_agent_name = Column(String(100), nullable=True)
    related_bill_id = Column(Integer, nullable=True)
    related_order_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    satisfaction_rating = Column(Integer, nullable=True)  # 1-5 stars
    satisfaction_comment = Column(Text, nullable=True)
    
    # Forwarding and Escalation fields
    forwarded_to_department = Column(String(50), nullable=True)  # maintenance, billing, monitoring, null if not forwarded
    forwarded_at = Column(DateTime, nullable=True)
    forwarded_by_user_id = Column(Integer, nullable=True)
    forwarded_by_name = Column(String(100), nullable=True)
    forwarded_service_order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=True)  # Created service order
    forwarded_bill_contest_id = Column(Integer, nullable=True)  # For billing department forwards
    escalation_level = Column(Integer, default=0)  # 0=normal, 1=escalated once, 2=escalated twice, etc.
    sla_deadline = Column(DateTime, nullable=True)  # When this ticket must be responded to
    last_escalation_at = Column(DateTime, nullable=True)
    escalation_reason = Column(String(500), nullable=True)
    
    # Relationships
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")
    forwarded_service_order = relationship("ServiceOrder", foreign_keys=[forwarded_service_order_id])

class TicketMessage(Base):
    __tablename__ = "ticket_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=False)
    message_type = Column(String(20), nullable=False)  # client, agent, system
    content = Column(Text, nullable=False)
    author_user_id = Column(Integer, nullable=True)
    author_name = Column(String(100), nullable=False)
    author_email = Column(String(100), nullable=True)
    is_internal = Column(Boolean, default=False)  # Internal notes for agents
    attachments = Column(Text, nullable=True)  # JSON list of file URLs
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ticket = relationship("SupportTicket", back_populates="messages")

class KnowledgeBaseArticle(Base):
    __tablename__ = "knowledge_base_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    slug = Column(String(250), unique=True, nullable=False)
    meta_description = Column(String(300), nullable=True)
    keywords = Column(String(500), nullable=True)
    created_by_user_id = Column(Integer, nullable=False)
    created_by_name = Column(String(100), nullable=False)
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    is_published = Column(Boolean, default=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SupportAgent(Base):
    __tablename__ = "support_agents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    department = Column(String(50), nullable=False)
    specialties = Column(String(200), nullable=True)  # JSON array of specialties
    is_active = Column(Boolean, default=True)
    max_concurrent_tickets = Column(Integer, default=10)
    current_ticket_count = Column(Integer, default=0)
    tickets_resolved = Column(Integer, default=0)
    satisfaction_average = Column(Float, default=0.0)
    average_response_time = Column(Float, default=0.0)  # in hours
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

# Maintenance Models
class ServiceOrder(Base):
    __tablename__ = "service_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    protocol_number = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String, nullable=False)  # AlertLevel enum
    location = Column(String, nullable=False)
    status = Column(String, default=ServiceOrderStatus.OPEN)  # ServiceOrderStatus enum
    created_by = Column(Integer, nullable=False)
    created_by_name = Column(String(100), nullable=True)
    assigned_team = Column(String, nullable=True)
    assigned_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_completion = Column(DateTime, nullable=True)
    actual_cost = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    anomaly_id = Column(Integer, nullable=True)  # Reference to monitoring service anomaly
    complaint_id = Column(Integer, nullable=True)  # Reference to complaint
    source_ticket_id = Column(Integer, nullable=True)  # Reference to support ticket that originated this order
    source_ticket_number = Column(String(30), nullable=True)  # Ticket number for easy reference
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ServiceOrderProgress(Base):
    __tablename__ = "service_order_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    service_order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=False)
    status = Column(String, nullable=False)
    progress_notes = Column(Text, nullable=False)
    estimated_completion = Column(DateTime, nullable=True)
    created_by = Column(Integer, nullable=False)
    created_by_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Maintenance(Base):
    __tablename__ = "maintenances"
    
    id = Column(Integer, primary_key=True, index=True)
    service_order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    team_name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    completion_date = Column(DateTime, nullable=False)
    duration_hours = Column(Float, nullable=True)
    cost = Column(Float, nullable=True)
    materials_used = Column(Text, nullable=True)
    equipment_used = Column(Text, nullable=True)
    work_type = Column(String, nullable=True)
    registered_by = Column(Integer, nullable=False)
    registered_by_name = Column(String(100), nullable=True)
    photos = Column(Text, nullable=True)  # JSON list of photo URLs
    quality_check = Column(Boolean, nullable=True)
    quality_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Complaint(Base):
    __tablename__ = "complaints"
    
    id = Column(Integer, primary_key=True, index=True)
    protocol_number = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    location = Column(String, nullable=False)
    citizen_name = Column(String, nullable=False)
    citizen_contact = Column(String, nullable=False)
    citizen_email = Column(String, nullable=True)
    urgency_level = Column(String, default="medium")  # AlertLevel enum
    status = Column(String, default="pending")
    assigned_to = Column(String, nullable=True)
    response_message = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    service_order_id = Column(Integer, nullable=True)
    photos = Column(Text, nullable=True)  # JSON list of photo URLs
    follow_up_required = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ServiceEvaluation(Base):
    __tablename__ = "service_evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    service_order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text, nullable=True)
    evaluator_name = Column(String, nullable=True)
    evaluator_contact = Column(String, nullable=True)
    quality_aspects = Column(Text, nullable=True)  # JSON object with quality ratings
    verified = Column(Boolean, default=False)
    moderator_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    specialization = Column(String, nullable=True)  # e.g., "plumbing", "electrical", "general"
    members_count = Column(Integer, default=0)
    max_concurrent_orders = Column(Integer, default=5)
    supervisor_name = Column(String(100), nullable=True)
    supervisor_contact = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    current_workload = Column(Integer, default=0)
    work_areas = Column(Text, nullable=True)  # JSON list of work areas
    equipment = Column(Text, nullable=True)  # JSON list of equipment
    performance_rating = Column(Float, nullable=True)
    completed_orders = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TeamMember(Base):
    __tablename__ = "team_members"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(100), nullable=True)
    contact = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Monitoring Models
class Sensor(Base):
    __tablename__ = "sensors"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    sensor_type = Column(String, nullable=False)  # SensorType enum
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    unit = Column(String, nullable=False)
    min_threshold = Column(Float, nullable=True)
    max_threshold = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    installation_date = Column(DateTime, nullable=True)
    manufacturer = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    calibration_date = Column(DateTime, nullable=True)
    maintenance_interval_days = Column(Integer, nullable=True)
    last_reading = Column(DateTime, nullable=True)
    battery_level = Column(Float, nullable=True)
    signal_strength = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, ForeignKey("sensors.id"), nullable=False)
    sensor_type = Column(String, nullable=False)  # SensorType enum
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    location = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    quality_score = Column(Float, nullable=True)
    battery_level = Column(Float, nullable=True)
    signal_strength = Column(Float, nullable=True)
    raw_data = Column(Text, nullable=True)  # JSON data
    is_anomaly = Column(Boolean, default=False)
    anomaly_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Anomaly(Base):
    __tablename__ = "anomalies"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, ForeignKey("sensors.id"), nullable=False)
    sensor_type = Column(String, nullable=False)  # SensorType enum
    value = Column(Float, nullable=False)
    threshold_value = Column(Float, nullable=False)
    severity = Column(String, nullable=False)  # AlertLevel enum
    description = Column(Text, nullable=False)
    location = Column(String, nullable=False)
    status = Column(String, default=AnomalyStatus.PENDING)  # AnomalyStatus enum
    operator_id = Column(Integer, nullable=True)
    operator_name = Column(String(100), nullable=True)
    assigned_operator_id = Column(Integer, nullable=True)
    reading_id = Column(Integer, nullable=True)
    detection_method = Column(String(50), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    additional_data = Column(Text, nullable=True)  # JSON data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Observation(Base):
    __tablename__ = "observations"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, ForeignKey("sensors.id"), nullable=False)
    reading_id = Column(Integer, nullable=True)  # Optional link to specific sensor reading
    operator_id = Column(Integer, nullable=False)
    operator_name = Column(String(100), nullable=True)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    observation_type = Column(String(50), nullable=True)
    severity = Column(String, default="low")  # AlertLevel enum
    photos = Column(Text, nullable=True)  # JSON list of photo URLs
    action_required = Column(Boolean, default=False)
    follow_up_notes = Column(Text, nullable=True)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LeakReport(Base):
    __tablename__ = "leak_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    protocol_number = Column(String, unique=True, nullable=False)
    location = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    reporter_name = Column(String, nullable=False)
    reporter_contact = Column(String, nullable=False)
    reporter_email = Column(String, nullable=True)
    urgency_level = Column(String, default="medium")  # AlertLevel enum
    estimated_size = Column(String(50), nullable=True)
    water_flow_stopped = Column(Boolean, default=False)
    status = Column(String, default="pending")  # LeakReportStatus enum
    assigned_team = Column(String(100), nullable=True)
    investigation_notes = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    estimated_repair_cost = Column(Float, nullable=True)
    actual_repair_cost = Column(Float, nullable=True)
    photos = Column(Text, nullable=True)  # JSON list of photo URLs
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


