"""
Billing calculation engine for water consumption
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
import sys

# Add shared modules to path
sys.path.append('/app/shared')
from models import BillStatus

from database_models import Customer, WaterMeter, MeterReading, Bill, TariffRate

class BillingCalculator:
    """Calculate water bills based on consumption and tariff rates"""
    
    def __init__(self):
        self.default_rates = {
            "residential": [
                {"tier_start": 0, "tier_end": 10, "rate": Decimal("2.50"), "fixed": Decimal("15.00")},
                {"tier_start": 10, "tier_end": 20, "rate": Decimal("3.00"), "fixed": Decimal("0.00")},
                {"tier_start": 20, "tier_end": 50, "rate": Decimal("4.50"), "fixed": Decimal("0.00")},
                {"tier_start": 50, "tier_end": None, "rate": Decimal("6.00"), "fixed": Decimal("0.00")}
            ],
            "commercial": [
                {"tier_start": 0, "tier_end": 50, "rate": Decimal("4.00"), "fixed": Decimal("25.00")},
                {"tier_start": 50, "tier_end": None, "rate": Decimal("5.50"), "fixed": Decimal("0.00")}
            ],
            "industrial": [
                {"tier_start": 0, "tier_end": None, "rate": Decimal("3.50"), "fixed": Decimal("50.00")}
            ]
        }
    
    async def generate_monthly_bill(self, customer_id: int, month: int, year: int, db: Session) -> Optional[Bill]:
        """Generate monthly bill for a customer"""
        try:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return None
            
            # Get customer's water meter
            meter = db.query(WaterMeter).filter(
                WaterMeter.customer_id == customer_id,
                WaterMeter.is_active == True
            ).first()
            if not meter:
                return None
            
            # Check if bill already exists for this period
            billing_start = datetime(year, month, 1)
            if month == 12:
                billing_end = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                billing_end = datetime(year, month + 1, 1) - timedelta(days=1)
            
            existing_bill = db.query(Bill).filter(
                Bill.customer_id == customer_id,
                Bill.billing_period_start == billing_start,
                Bill.billing_period_end == billing_end
            ).first()
            if existing_bill:
                return existing_bill
            
            # Get consumption for the period
            consumption = await self._calculate_consumption(meter.meter_id, billing_start, billing_end, db)
            
            # Calculate bill amount
            amount = await self._calculate_bill_amount(customer.customer_type, consumption, db)
            
            # Create bill
            due_date = billing_end + timedelta(days=30)  # 30 days to pay
            
            bill = Bill(
                customer_id=customer_id,
                meter_id=meter.meter_id,
                amount=amount,
                consumption=consumption,
                billing_period_start=billing_start,
                billing_period_end=billing_end,
                due_date=due_date,
                status=BillStatus.PENDING
            )
            
            db.add(bill)
            db.commit()
            db.refresh(bill)
            
            return bill
            
        except Exception as e:
            print(f"Error generating bill for customer {customer_id}: {e}")
            return None
    
    async def _calculate_consumption(self, meter_id: str, start_date: datetime, end_date: datetime, db: Session) -> float:
        """Calculate water consumption for a period"""
        try:
            # Get readings for the period
            readings = db.query(MeterReading).filter(
                MeterReading.meter_id == meter_id,
                MeterReading.reading_date >= start_date,
                MeterReading.reading_date <= end_date
            ).order_by(MeterReading.reading_date).all()
            
            if len(readings) < 2:
                # If we don't have enough readings, estimate based on average
                return await self._estimate_consumption(meter_id, db)
            
            # Calculate consumption as difference between first and last reading
            first_reading = readings[0].reading_value
            last_reading = readings[-1].reading_value
            consumption = last_reading - first_reading
            
            return max(0, consumption)  # Ensure non-negative
            
        except Exception as e:
            print(f"Error calculating consumption: {e}")
            return 0.0
    
    async def _estimate_consumption(self, meter_id: str, db: Session) -> float:
        """Estimate consumption based on historical average"""
        try:
            # Get last 6 months of readings
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            readings = db.query(MeterReading).filter(
                MeterReading.meter_id == meter_id,
                MeterReading.reading_date >= six_months_ago
            ).order_by(MeterReading.reading_date).all()
            
            if len(readings) < 2:
                return 15.0  # Default estimate for residential
            
            # Calculate average monthly consumption
            total_consumption = readings[-1].reading_value - readings[0].reading_value
            months = len(readings) / 30  # Approximate months
            average_monthly = total_consumption / max(1, months)
            
            return max(5.0, average_monthly)  # Minimum 5m³
            
        except Exception as e:
            print(f"Error estimating consumption: {e}")
            return 15.0
    
    async def _calculate_bill_amount(self, customer_type: str, consumption: float, db: Session) -> Decimal:
        """Calculate bill amount based on consumption and tariff rates"""
        try:
            # Get active tariff rates from database
            tariffs = db.query(TariffRate).filter(
                TariffRate.customer_type == customer_type,
                TariffRate.is_active == True
            ).order_by(TariffRate.tier_start).all()
            
            # If no tariffs in database, use default rates
            if not tariffs:
                rates = self.default_rates.get(customer_type, self.default_rates["residential"])
                return self._apply_tiered_rates(consumption, rates)
            
            # Apply database tariff rates
            total_amount = Decimal('0.00')
            remaining_consumption = consumption
            
            for tariff in tariffs:
                if remaining_consumption <= 0:
                    break
                
                tier_consumption = remaining_consumption
                if tariff.tier_end:
                    tier_consumption = min(remaining_consumption, tariff.tier_end - tariff.tier_start)
                
                tier_amount = Decimal(str(tier_consumption)) * tariff.rate_per_m3
                total_amount += tier_amount + tariff.fixed_charge
                
                remaining_consumption -= tier_consumption
            
            return total_amount
            
        except Exception as e:
            print(f"Error calculating bill amount: {e}")
            return Decimal('50.00')  # Default amount
    
    def _apply_tiered_rates(self, consumption: float, rates: list) -> Decimal:
        """Apply tiered rate structure"""
        total_amount = Decimal('0.00')
        remaining_consumption = consumption
        
        for rate in rates:
            if remaining_consumption <= 0:
                break
            
            tier_consumption = remaining_consumption
            if rate["tier_end"]:
                tier_consumption = min(remaining_consumption, rate["tier_end"] - rate["tier_start"])
            
            tier_amount = Decimal(str(tier_consumption)) * rate["rate"]
            total_amount += tier_amount + rate["fixed"]
            
            remaining_consumption -= tier_consumption
        
        return total_amount
    
    async def calculate_late_fees(self, bill: Bill) -> Decimal:
        """Calculate late fees for overdue bills"""
        if bill.status != BillStatus.OVERDUE:
            return Decimal('0.00')
        
        days_overdue = (datetime.utcnow() - bill.due_date).days
        if days_overdue <= 0:
            return Decimal('0.00')
        
        # 2% per month (0.067% per day) + fixed fee
        daily_rate = Decimal('0.0007')  # 0.07% per day
        fixed_fee = Decimal('5.00')
        
        late_fee = (bill.amount * daily_rate * days_overdue) + fixed_fee
        return min(late_fee, bill.amount * Decimal('0.5'))  # Max 50% of original amount
    
    async def calculate_negotiation_terms(self, total_debt: Decimal, installments: int) -> dict:
        """Calculate debt negotiation terms"""
        # Base discount based on number of installments
        discount_map = {
            1: 0.15,  # 15% discount for full payment
            2: 0.10,  # 10% discount for 2 installments
            3: 0.08,  # 8% discount for 3 installments
            6: 0.05,  # 5% discount for 6 installments
            12: 0.02  # 2% discount for 12 installments
        }
        
        discount_rate = discount_map.get(installments, 0.0)
        if installments > 12:
            discount_rate = 0.0
            interest_rate = 0.01  # 1% per month for long-term
        else:
            interest_rate = 0.0
        
        discounted_amount = total_debt * (1 - Decimal(str(discount_rate)))
        installment_amount = discounted_amount / installments
        
        return {
            "total_debt": total_debt,
            "discount_percentage": discount_rate * 100,
            "discounted_amount": discounted_amount,
            "installments": installments,
            "installment_amount": installment_amount,
            "interest_rate": interest_rate * 100
        }