#!/usr/bin/env python3
"""
FIX REVENUE SYSTEM v9.30
Complete repair of payment, AI, and automation systems
Target: 100% revenue capability TODAY
"""

import os
import sys
import json
import stripe
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL')

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Stripe configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "<STRIPE_KEY_REDACTED>")
stripe.api_key = STRIPE_SECRET_KEY

def fix_database_tables():
    """Create all missing tables for revenue system"""
    print("🔧 Creating/fixing database tables...")
    
    with Session() as session:
        # Create subscriptions table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                customer_id UUID REFERENCES customers(id),
                stripe_subscription_id VARCHAR(255) UNIQUE,
                stripe_customer_id VARCHAR(255),
                status VARCHAR(50) DEFAULT 'active',
                plan_id VARCHAR(100),
                plan_name VARCHAR(255),
                price_amount INTEGER, -- in cents
                currency VARCHAR(10) DEFAULT 'usd',
                interval VARCHAR(20) DEFAULT 'month',
                current_period_start TIMESTAMP,
                current_period_end TIMESTAMP,
                cancel_at_period_end BOOLEAN DEFAULT FALSE,
                canceled_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        
        # Create products table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS products (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                stripe_product_id VARCHAR(255) UNIQUE,
                stripe_price_id VARCHAR(255) UNIQUE,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                price_amount INTEGER NOT NULL, -- in cents
                currency VARCHAR(10) DEFAULT 'usd',
                interval VARCHAR(20),
                features JSONB,
                metadata JSONB,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        
        # Create payment_methods table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS payment_methods (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                customer_id UUID REFERENCES customers(id),
                stripe_payment_method_id VARCHAR(255) UNIQUE,
                type VARCHAR(50),
                last4 VARCHAR(4),
                brand VARCHAR(50),
                exp_month INTEGER,
                exp_year INTEGER,
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        
        # Create invoices enhancements
        session.execute(text("""
            ALTER TABLE invoices 
            ADD COLUMN IF NOT EXISTS stripe_invoice_id VARCHAR(255),
            ADD COLUMN IF NOT EXISTS stripe_payment_intent_id VARCHAR(255),
            ADD COLUMN IF NOT EXISTS payment_status VARCHAR(50) DEFAULT 'pending',
            ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50),
            ADD COLUMN IF NOT EXISTS paid_at TIMESTAMP
        """))
        
        # Create ai_agents table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_agents (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                type VARCHAR(100),
                status VARCHAR(50) DEFAULT 'active',
                capabilities JSONB,
                configuration JSONB,
                last_active TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        
        # Create automations table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS automations (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                type VARCHAR(100),
                trigger_type VARCHAR(100),
                conditions JSONB,
                actions JSONB,
                status VARCHAR(50) DEFAULT 'active',
                last_run TIMESTAMP,
                run_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        
        # Create neural_pathways table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS neural_pathways (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                source_agent_id UUID REFERENCES ai_agents(id),
                target_agent_id UUID REFERENCES ai_agents(id),
                pathway_type VARCHAR(100),
                strength FLOAT DEFAULT 1.0,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        
        # Create langgraph_workflows table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS langgraph_workflows (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                graph_definition JSONB,
                status VARCHAR(50) DEFAULT 'active',
                version VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        
        # Create ai_memory table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_memory (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                agent_id UUID REFERENCES ai_agents(id),
                memory_type VARCHAR(100),
                key VARCHAR(255),
                value JSONB,
                importance FLOAT DEFAULT 0.5,
                created_at TIMESTAMP DEFAULT NOW(),
                accessed_at TIMESTAMP DEFAULT NOW()
            )
        """))
        
        # Create revenue_events table for tracking
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS revenue_events (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                event_type VARCHAR(100),
                customer_id UUID REFERENCES customers(id),
                amount INTEGER, -- in cents
                currency VARCHAR(10) DEFAULT 'usd',
                metadata JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        
        session.commit()
        print("✅ Database tables created/fixed")

def create_stripe_products():
    """Create Stripe products and prices"""
    print("💳 Creating Stripe products...")
    
    products = [
        {
            "name": "MyRoofGenius Starter",
            "description": "Perfect for small roofing contractors",
            "price": 9700,  # $97
            "features": [
                "AI-powered estimates",
                "Basic CRM",
                "Mobile app",
                "Email support"
            ]
        },
        {
            "name": "MyRoofGenius Professional",
            "description": "For growing roofing businesses",
            "price": 29700,  # $297
            "features": [
                "Everything in Starter",
                "Advanced AI analytics",
                "Team collaboration",
                "Priority support",
                "Custom branding"
            ]
        },
        {
            "name": "MyRoofGenius Enterprise",
            "description": "For large roofing companies",
            "price": 99700,  # $997
            "features": [
                "Everything in Professional",
                "Unlimited users",
                "API access",
                "Dedicated account manager",
                "Custom integrations"
            ]
        }
    ]
    
    with Session() as session:
        for product_data in products:
            try:
                # Create product in Stripe
                stripe_product = stripe.Product.create(
                    name=product_data["name"],
                    description=product_data["description"],
                    metadata={"features": json.dumps(product_data["features"])}
                )
                
                # Create price in Stripe
                stripe_price = stripe.Price.create(
                    product=stripe_product.id,
                    unit_amount=product_data["price"],
                    currency="usd",
                    recurring={"interval": "month"}
                )
                
                # Save to database
                session.execute(text("""
                    INSERT INTO products (
                        stripe_product_id, stripe_price_id, name, description,
                        price_amount, currency, interval, features, active
                    ) VALUES (
                        :product_id, :price_id, :name, :description,
                        :amount, 'usd', 'month', :features, TRUE
                    )
                    ON CONFLICT (stripe_product_id) DO UPDATE SET
                        stripe_price_id = EXCLUDED.stripe_price_id,
                        price_amount = EXCLUDED.price_amount
                """), {
                    "product_id": stripe_product.id,
                    "price_id": stripe_price.id,
                    "name": product_data["name"],
                    "description": product_data["description"],
                    "amount": product_data["price"],
                    "features": json.dumps(product_data["features"])
                })
                
                print(f"✅ Created product: {product_data['name']}")
                
            except stripe.error.StripeError as e:
                print(f"⚠️ Stripe error for {product_data['name']}: {e}")
            except Exception as e:
                print(f"⚠️ Error creating {product_data['name']}: {e}")
        
        session.commit()

def populate_ai_agents():
    """Populate AI agents for the system"""
    print("🤖 Populating AI agents...")
    
    agents = [
        {
            "name": "Sophie",
            "type": "customer_support",
            "model": "gpt-4",
            "capabilities": ["chat", "email", "knowledge_base", "ticket_routing"]
        },
        {
            "name": "Max",
            "type": "sales_optimization",
            "model": "claude-3",
            "capabilities": ["lead_scoring", "opportunity_tracking", "proposal_generation"]
        },
        {
            "name": "Elena",
            "type": "estimation_expert",
            "model": "gpt-4",
            "capabilities": ["roof_analysis", "cost_calculation", "material_planning"]
        },
        {
            "name": "Victoria",
            "type": "business_strategist",
            "model": "claude-3",
            "capabilities": ["analytics", "forecasting", "optimization", "reporting"]
        },
        {
            "name": "AUREA",
            "type": "executive_assistant",
            "model": "claude-3-opus",
            "capabilities": ["task_management", "scheduling", "communication", "decision_support"]
        },
        {
            "name": "BrainLink",
            "type": "neural_coordinator",
            "model": "gpt-4",
            "capabilities": ["agent_orchestration", "workflow_management", "learning"]
        }
    ]
    
    with Session() as session:
        for agent_data in agents:
            # Check if agent already exists
            existing = session.execute(text("""
                SELECT id FROM ai_agents WHERE name = :name
            """), {"name": agent_data["name"]}).fetchone()
            
            if not existing:
                session.execute(text("""
                    INSERT INTO ai_agents (name, type, model, status, capabilities)
                    VALUES (:name, :type, :model, 'active', :capabilities)
                """), {
                    "name": agent_data["name"],
                    "type": agent_data["type"],
                    "model": agent_data["model"],
                    "capabilities": json.dumps(agent_data["capabilities"])
                })
        
        session.commit()
        print("✅ AI agents populated")

def create_automations():
    """Create automation workflows"""
    print("⚙️ Creating automation workflows...")
    
    automations = [
        {
            "name": "New Lead Welcome",
            "type": "email_sequence",
            "trigger_type": "new_lead",
            "actions": ["send_welcome_email", "create_crm_contact", "assign_to_sales"]
        },
        {
            "name": "Quote Follow-up",
            "type": "follow_up",
            "trigger_type": "quote_sent",
            "actions": ["wait_3_days", "send_follow_up", "create_task"]
        },
        {
            "name": "Payment Failed",
            "type": "revenue_recovery",
            "trigger_type": "payment_failed",
            "actions": ["send_retry_email", "update_card_request", "notify_team"]
        },
        {
            "name": "Customer Onboarding",
            "type": "onboarding",
            "trigger_type": "subscription_created",
            "actions": ["send_welcome_kit", "schedule_onboarding_call", "create_account"]
        }
    ]
    
    with Session() as session:
        for auto_data in automations:
            session.execute(text("""
                INSERT INTO automations (name, type, trigger_type, actions, status)
                VALUES (:name, :type, :trigger, :actions, 'active')
                ON CONFLICT DO NOTHING
            """), {
                "name": auto_data["name"],
                "type": auto_data["type"],
                "trigger": auto_data["trigger_type"],
                "actions": json.dumps(auto_data["actions"])
            })
        
        session.commit()
        print("✅ Automations created")

def create_langgraph_workflows():
    """Create LangGraph workflow definitions"""
    print("🔄 Creating LangGraph workflows...")
    
    workflows = [
        {
            "name": "Customer Journey",
            "graph_definition": {
                "nodes": ["lead", "prospect", "customer", "advocate"],
                "edges": [
                    ["lead", "prospect"],
                    ["prospect", "customer"],
                    ["customer", "advocate"]
                ]
            }
        },
        {
            "name": "Revenue Pipeline",
            "graph_definition": {
                "nodes": ["inquiry", "quote", "negotiation", "closed"],
                "edges": [
                    ["inquiry", "quote"],
                    ["quote", "negotiation"],
                    ["negotiation", "closed"]
                ]
            }
        },
        {
            "name": "Service Delivery",
            "graph_definition": {
                "nodes": ["scheduled", "in_progress", "completed", "paid"],
                "edges": [
                    ["scheduled", "in_progress"],
                    ["in_progress", "completed"],
                    ["completed", "paid"]
                ]
            }
        }
    ]
    
    with Session() as session:
        for workflow in workflows:
            session.execute(text("""
                INSERT INTO langgraph_workflows (name, graph_definition, status, version)
                VALUES (:name, :definition, 'active', '1.0')
                ON CONFLICT DO NOTHING
            """), {
                "name": workflow["name"],
                "definition": json.dumps(workflow["graph_definition"])
            })
        
        session.commit()
        print("✅ LangGraph workflows created")

def create_neural_pathways():
    """Create neural pathways between AI agents"""
    print("🧠 Creating neural pathways...")
    
    with Session() as session:
        # Get all agents
        agents = session.execute(text("SELECT id, name FROM ai_agents")).fetchall()
        agent_map = {agent.name: agent.id for agent in agents}
        
        # Define pathways
        pathways = [
            ("Sophie", "AUREA", "escalation"),
            ("Max", "Elena", "estimation_request"),
            ("Elena", "Victoria", "analytics_feed"),
            ("Victoria", "AUREA", "strategic_insight"),
            ("AUREA", "BrainLink", "coordination"),
            ("BrainLink", "Sophie", "customer_routing"),
            ("BrainLink", "Max", "lead_routing"),
            ("BrainLink", "Elena", "estimation_routing"),
            ("BrainLink", "Victoria", "analytics_routing")
        ]
        
        for source, target, pathway_type in pathways:
            if source in agent_map and target in agent_map:
                session.execute(text("""
                    INSERT INTO neural_pathways (source_agent_id, target_agent_id, pathway_type, strength)
                    VALUES (:source, :target, :type, 1.0)
                    ON CONFLICT DO NOTHING
                """), {
                    "source": agent_map[source],
                    "target": agent_map[target],
                    "type": pathway_type
                })
        
        session.commit()
        print("✅ Neural pathways established")

def create_sample_subscription():
    """Create a sample subscription for testing"""
    print("💰 Creating sample subscription...")
    
    with Session() as session:
        # Get or create a test customer
        result = session.execute(text("""
            INSERT INTO customers (name, email, phone, company)
            VALUES ('Test Customer', 'test@myroofgenius.com', '555-0100', 'Test Roofing Co')
            ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
        """)).fetchone()
        
        if result:
            customer_id = result[0]
            
            # Create a subscription
            session.execute(text("""
                INSERT INTO subscriptions (
                    customer_id, status, plan_id, plan_name, 
                    price_amount, currency, interval
                ) VALUES (
                    :customer_id, 'active', 'professional', 'MyRoofGenius Professional',
                    29700, 'usd', 'month'
                )
                ON CONFLICT DO NOTHING
            """), {"customer_id": customer_id})
            
            session.commit()
            print("✅ Sample subscription created")

def main():
    """Main execution"""
    print("=" * 60)
    print("🚀 REVENUE SYSTEM FIX v9.30")
    print("=" * 60)
    
    try:
        # Fix database
        fix_database_tables()
        
        # Create products
        create_stripe_products()
        
        # Populate AI systems
        populate_ai_agents()
        create_automations()
        create_langgraph_workflows()
        create_neural_pathways()
        
        # Create sample data
        create_sample_subscription()
        
        print("\n" + "=" * 60)
        print("✅ REVENUE SYSTEM FIXED!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Update backend routes to use these tables")
        print("2. Deploy v9.30 to production")
        print("3. Test payment flow end-to-end")
        print("4. Launch customer acquisition")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()