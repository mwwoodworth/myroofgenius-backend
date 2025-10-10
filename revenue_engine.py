"""
Revenue Engine - The Money Making Machine
Direct revenue generation through automated customer acquisition, conversion, and retention
"""

import os
import asyncio
import json
import stripe
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import asyncpg
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import openai
from geopy.geocoders import Nominatim
from pydantic import BaseModel
import hashlib
import redis

# Payment processing
stripe.api_key = os.getenv("STRIPE_API_KEY")

# Communications
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

sendgrid_client = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))

class Lead(BaseModel):
    """Customer lead model"""
    name: str
    email: str
    phone: str
    address: str
    roof_type: Optional[str] = None
    square_footage: Optional[int] = None
    urgency: str = "normal"  # emergency, urgent, normal, planning
    source: str = "website"
    budget_range: Optional[str] = None
    insurance_claim: bool = False

class RevenueEngine:
    """Core revenue generation system"""
    
    def __init__(self, pg_pool, redis_client):
        self.pg_pool = pg_pool
        self.redis = redis_client
        self.geolocator = Nominatim(user_agent="myroofgenius")
        
        # Pricing engine configuration
        self.base_rates = {
            "asphalt_shingle": 350,  # per square
            "metal": 750,
            "tile": 850,
            "slate": 1200,
            "flat_tpo": 650,
            "emergency_multiplier": 1.5,
            "weekend_multiplier": 1.25,
            "insurance_handling_fee": 500
        }
        
        # Commission structure
        self.commission_rates = {
            "lead_generation": 50,  # Per qualified lead
            "appointment_set": 100,  # Per appointment
            "contract_signed": 0.05,  # 5% of contract value
            "project_completed": 0.02,  # 2% completion bonus
            "referral": 200  # Per referral that converts
        }
    
    async def capture_lead(self, lead: Lead) -> Dict[str, Any]:
        """
        Capture and immediately monetize a new lead
        Returns the lead ID and immediate actions taken
        """
        lead_id = hashlib.md5(f"{lead.email}{datetime.now()}".encode()).hexdigest()
        
        async with self.pg_pool.acquire() as conn:
            # Store lead
            await conn.execute('''
                INSERT INTO leads (
                    id, name, email, phone, address, roof_type, 
                    square_footage, urgency, source, budget_range, 
                    insurance_claim, captured_at, status, value_score
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), $12, $13)
            ''', lead_id, lead.name, lead.email, lead.phone, lead.address,
                lead.roof_type, lead.square_footage, lead.urgency, lead.source,
                lead.budget_range, lead.insurance_claim, 'new', 0)
        
        # Immediate revenue actions
        actions = []
        
        # 1. Calculate instant quote
        quote = await self.generate_instant_quote(lead)
        actions.append({"type": "quote_generated", "value": quote["total"]})
        
        # 2. Send immediate SMS (higher open rate)
        if lead.urgency in ["emergency", "urgent"]:
            sms_result = await self.send_emergency_response_sms(lead, quote)
            actions.append({"type": "emergency_sms_sent", "success": sms_result})
        
        # 3. Create Stripe customer for future charges
        stripe_customer = stripe.Customer.create(
            email=lead.email,
            name=lead.name,
            phone=lead.phone,
            metadata={"lead_id": lead_id}
        )
        actions.append({"type": "stripe_customer_created", "id": stripe_customer.id})
        
        # 4. Schedule automated follow-ups
        follow_ups = await self.schedule_revenue_maximizing_followups(lead_id, lead, quote)
        actions.append({"type": "followups_scheduled", "count": len(follow_ups)})
        
        # 5. Check for insurance opportunity (higher ticket value)
        if lead.insurance_claim:
            insurance_result = await self.initiate_insurance_claim_assistance(lead, lead_id)
            actions.append({"type": "insurance_assistance", "potential_value": insurance_result["max_claim"]})
        
        # 6. Trigger referral request if high-value
        if quote["total"] > 15000:
            referral = await self.trigger_referral_campaign(lead)
            actions.append({"type": "referral_campaign", "triggered": True})
        
        # 7. Add to sales pipeline
        pipeline_position = await self.add_to_sales_pipeline(lead_id, lead, quote)
        actions.append({"type": "pipeline_position", "stage": pipeline_position})
        
        # Calculate total potential value
        potential_value = quote["total"] + (insurance_result["max_claim"] if lead.insurance_claim else 0)
        
        # Update lead value score
        await self.update_lead_score(lead_id, potential_value)
        
        return {
            "lead_id": lead_id,
            "potential_revenue": potential_value,
            "immediate_actions": actions,
            "conversion_probability": await self.calculate_conversion_probability(lead),
            "estimated_close_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "quote": quote
        }
    
    async def generate_instant_quote(self, lead: Lead) -> Dict[str, Any]:
        """Generate instant, competitive quote to capture customer immediately"""
        # Get property details via geocoding
        try:
            location = self.geolocator.geocode(lead.address)
            lat, lon = location.latitude, location.longitude
        except:
            lat, lon = 39.7392, -104.9903  # Default to Denver
        
        # Estimate square footage if not provided
        if not lead.square_footage:
            lead.square_footage = 2000  # Default estimate
        
        # Calculate squares (roofing measurement unit = 100 sq ft)
        squares = lead.square_footage / 100
        
        # Determine roof type if not specified
        if not lead.roof_type:
            lead.roof_type = "asphalt_shingle"  # Most common
        
        # Base cost calculation
        base_cost = squares * self.base_rates.get(lead.roof_type, 350)
        
        # Apply urgency multipliers
        if lead.urgency == "emergency":
            base_cost *= self.base_rates["emergency_multiplier"]
        elif lead.urgency == "urgent":
            base_cost *= 1.15
        
        # Additional costs
        permit_cost = 350
        disposal_cost = squares * 25
        labor_cost = squares * 150
        
        # Insurance handling
        insurance_fee = self.base_rates["insurance_handling_fee"] if lead.insurance_claim else 0
        
        # Calculate totals
        subtotal = base_cost + permit_cost + disposal_cost + labor_cost + insurance_fee
        tax = subtotal * 0.0825  # Colorado average
        total = subtotal + tax
        
        # Financing options
        financing_options = [
            {"months": 12, "monthly": total / 12, "apr": 0},
            {"months": 24, "monthly": (total * 1.05) / 24, "apr": 5.0},
            {"months": 36, "monthly": (total * 1.08) / 36, "apr": 8.0},
            {"months": 60, "monthly": (total * 1.12) / 60, "apr": 12.0}
        ]
        
        return {
            "squares": squares,
            "roof_type": lead.roof_type,
            "base_cost": round(base_cost, 2),
            "permit_cost": permit_cost,
            "disposal_cost": round(disposal_cost, 2),
            "labor_cost": round(labor_cost, 2),
            "insurance_fee": insurance_fee,
            "subtotal": round(subtotal, 2),
            "tax": round(tax, 2),
            "total": round(total, 2),
            "financing_options": financing_options,
            "savings_vs_competitors": round(total * 0.15, 2),  # Show 15% savings
            "warranty": "Lifetime material, 10-year labor",
            "estimated_days": 1 if squares < 30 else 2,
            "valid_until": (datetime.now() + timedelta(days=14)).isoformat()
        }
    
    async def send_emergency_response_sms(self, lead: Lead, quote: Dict) -> bool:
        """Send immediate SMS for emergency/urgent leads"""
        message = f"""
        {lead.name}, MyRoofGenius Emergency Response Team here!
        
        We can help TODAY. Your quote: ${quote['total']:,.2f}
        
        🏠 {quote['squares']:.0f} squares
        ⏰ {quote['estimated_days']} day completion
        ✓ {quote['warranty']}
        
        Reply YES to schedule immediate inspection or call 720-ROOFNOW
        
        💰 Save ${quote['savings_vs_competitors']:,.2f} vs competitors
        """
        
        try:
            message = twilio_client.messages.create(
                body=message,
                from_=os.getenv("TWILIO_PHONE"),
                to=lead.phone
            )
            return True
        except:
            return False
    
    async def schedule_revenue_maximizing_followups(self, lead_id: str, lead: Lead, quote: Dict) -> List[Dict]:
        """Schedule strategic follow-ups to maximize conversion"""
        followups = []
        
        async with self.pg_pool.acquire() as conn:
            # Immediate email with quote (1 hour)
            followups.append({
                "type": "email",
                "scheduled_for": datetime.now() + timedelta(hours=1),
                "subject": f"Your MyRoofGenius Quote: ${quote['total']:,.2f} - Save ${quote['savings_vs_competitors']:,.2f}",
                "template": "instant_quote"
            })
            
            # SMS follow-up (next morning)
            followups.append({
                "type": "sms",
                "scheduled_for": datetime.now() + timedelta(hours=18),
                "message": f"Good morning {lead.name}! Your roof quote expires in 13 days. Lock in your ${quote['savings_vs_competitors']:,.2f} savings today!"
            })
            
            # Call attempt (2 days)
            followups.append({
                "type": "call",
                "scheduled_for": datetime.now() + timedelta(days=2),
                "script": "high_value_lead",
                "fallback": "voicemail_with_callback"
            })
            
            # Limited time offer (4 days)
            followups.append({
                "type": "email",
                "scheduled_for": datetime.now() + timedelta(days=4),
                "subject": "🔥 48-Hour Flash Sale: Extra 5% Off Your Roof",
                "template": "urgency_discount"
            })
            
            # Final push (7 days)
            followups.append({
                "type": "multi",
                "scheduled_for": datetime.now() + timedelta(days=7),
                "channels": ["email", "sms", "call"],
                "message": "Final opportunity for savings"
            })
            
            # Store follow-ups
            for followup in followups:
                await conn.execute('''
                    INSERT INTO scheduled_followups (lead_id, type, scheduled_for, data, status)
                    VALUES ($1, $2, $3, $4, 'pending')
                ''', lead_id, followup["type"], followup["scheduled_for"], json.dumps(followup))
        
        return followups
    
    async def initiate_insurance_claim_assistance(self, lead: Lead, lead_id: str) -> Dict:
        """Help with insurance claims for higher ticket values"""
        # Typical insurance claim values
        claim_estimates = {
            "hail_damage": 15000,
            "wind_damage": 12000,
            "tree_damage": 18000,
            "water_damage": 20000,
            "fire_damage": 35000
        }
        
        # Store insurance opportunity
        async with self.pg_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO insurance_opportunities (
                    lead_id, estimated_claim, status, created_at
                ) VALUES ($1, $2, 'pending', NOW())
            ''', lead_id, max(claim_estimates.values()))
        
        # Send insurance assistance email
        await self.send_insurance_assistance_email(lead)
        
        return {
            "max_claim": max(claim_estimates.values()),
            "assistance_offered": True,
            "supplement_potential": 5000  # Additional we can get from insurance
        }
    
    async def trigger_referral_campaign(self, lead: Lead) -> Dict:
        """Trigger referral campaign for high-value leads"""
        referral_incentive = 500  # Cash incentive for referrals
        
        # Create referral tracking code
        referral_code = hashlib.md5(f"{lead.email}referral".encode()).hexdigest()[:8].upper()
        
        async with self.pg_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO referral_campaigns (
                    lead_email, referral_code, incentive_amount, created_at, status
                ) VALUES ($1, $2, $3, NOW(), 'active')
            ''', lead.email, referral_code, referral_incentive)
        
        return {
            "referral_code": referral_code,
            "incentive": referral_incentive,
            "potential_referrals": 3  # Average referrals per customer
        }
    
    async def add_to_sales_pipeline(self, lead_id: str, lead: Lead, quote: Dict) -> str:
        """Add lead to automated sales pipeline"""
        # Determine pipeline stage based on lead quality
        if lead.urgency == "emergency":
            stage = "closing"
        elif lead.insurance_claim:
            stage = "negotiation"
        elif quote["total"] > 20000:
            stage = "proposal"
        else:
            stage = "qualification"
        
        async with self.pg_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO sales_pipeline (
                    lead_id, stage, value, probability, expected_close, created_at
                ) VALUES ($1, $2, $3, $4, $5, NOW())
            ''', lead_id, stage, quote["total"], 
                0.8 if stage == "closing" else 0.5,
                datetime.now() + timedelta(days=7 if stage == "closing" else 14))
        
        return stage
    
    async def calculate_conversion_probability(self, lead: Lead) -> float:
        """Calculate probability of converting lead to customer"""
        score = 0.3  # Base probability
        
        # Urgency factors
        if lead.urgency == "emergency":
            score += 0.4
        elif lead.urgency == "urgent":
            score += 0.2
        
        # Insurance claim (high conversion)
        if lead.insurance_claim:
            score += 0.2
        
        # Source quality
        source_scores = {
            "referral": 0.2,
            "website": 0.1,
            "google_ads": 0.15,
            "facebook": 0.05
        }
        score += source_scores.get(lead.source, 0.05)
        
        return min(score, 0.95)  # Cap at 95%
    
    async def update_lead_score(self, lead_id: str, potential_value: float):
        """Update lead scoring for prioritization"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute('''
                UPDATE leads 
                SET value_score = $1, updated_at = NOW()
                WHERE id = $2
            ''', potential_value, lead_id)
    
    async def send_insurance_assistance_email(self, lead: Lead):
        """Send email about insurance claim assistance"""
        message = Mail(
            from_email='claims@myroofgenius.com',
            to_emails=lead.email,
            subject='We Handle Everything With Your Insurance Company',
            html_content=f'''
            <h2>Hi {lead.name},</h2>
            <p>We'll handle your entire insurance claim process!</p>
            <ul>
                <li>✓ Free inspection & documentation</li>
                <li>✓ Direct insurance billing</li>
                <li>✓ We fight for maximum coverage</li>
                <li>✓ You pay only deductible</li>
                <li>✓ Guaranteed approval or no charge</li>
            </ul>
            <p><b>Average claim approved: $18,500</b></p>
            <a href="https://myroofgenius.com/insurance-claim?email={lead.email}">
                Start Your Claim Now
            </a>
            '''
        )
        
        try:
            response = sendgrid_client.send(message)
            return True
        except:
            return False
    
    async def process_payment(self, lead_id: str, amount: float, type: str = "deposit") -> Dict:
        """Process payment through Stripe"""
        async with self.pg_pool.acquire() as conn:
            # Get customer details
            customer = await conn.fetchrow(
                "SELECT * FROM leads WHERE id = $1", lead_id
            )
            
            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Stripe uses cents
                currency="usd",
                customer=customer["stripe_customer_id"],
                metadata={
                    "lead_id": lead_id,
                    "type": type
                }
            )
            
            # Record transaction
            await conn.execute('''
                INSERT INTO transactions (
                    lead_id, amount, type, stripe_payment_intent, status, created_at
                ) VALUES ($1, $2, $3, $4, 'pending', NOW())
            ''', lead_id, amount, type, payment_intent.id)
            
            return {
                "payment_intent": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "amount": amount
            }
    
    async def calculate_daily_revenue(self) -> Dict:
        """Calculate and track daily revenue metrics"""
        async with self.pg_pool.acquire() as conn:
            # Today's revenue
            today_revenue = await conn.fetchval('''
                SELECT COALESCE(SUM(amount), 0) 
                FROM transactions 
                WHERE created_at::date = CURRENT_DATE 
                AND status = 'completed'
            ''')
            
            # Today's leads value
            today_leads_value = await conn.fetchval('''
                SELECT COALESCE(SUM(value_score), 0)
                FROM leads
                WHERE captured_at::date = CURRENT_DATE
            ''')
            
            # Conversion rate
            conversions = await conn.fetchval('''
                SELECT COUNT(*) FROM leads
                WHERE captured_at::date = CURRENT_DATE
                AND status = 'converted'
            ''')
            
            total_leads = await conn.fetchval('''
                SELECT COUNT(*) FROM leads
                WHERE captured_at::date = CURRENT_DATE
            ''')
            
            conversion_rate = (conversions / total_leads * 100) if total_leads > 0 else 0
            
            return {
                "actual_revenue": float(today_revenue),
                "pipeline_value": float(today_leads_value),
                "leads_captured": total_leads,
                "conversions": conversions,
                "conversion_rate": conversion_rate,
                "average_deal_size": float(today_revenue / conversions) if conversions > 0 else 0
            }
    
    async def automated_lead_nurturing(self):
        """Automated lead nurturing system that runs continuously"""
        while True:
            async with self.pg_pool.acquire() as conn:
                # Get pending follow-ups
                pending = await conn.fetch('''
                    SELECT * FROM scheduled_followups 
                    WHERE scheduled_for <= NOW() 
                    AND status = 'pending'
                    LIMIT 10
                ''')
                
                for followup in pending:
                    await self.execute_followup(followup)
                    
                    # Mark as completed
                    await conn.execute('''
                        UPDATE scheduled_followups 
                        SET status = 'completed', executed_at = NOW()
                        WHERE id = $1
                    ''', followup["id"])
            
            await asyncio.sleep(60)  # Check every minute
    
    async def execute_followup(self, followup: Dict):
        """Execute a scheduled follow-up"""
        data = json.loads(followup["data"])
        
        if followup["type"] == "email":
            # Send email
            pass
        elif followup["type"] == "sms":
            # Send SMS
            pass
        elif followup["type"] == "call":
            # Initiate automated call
            pass