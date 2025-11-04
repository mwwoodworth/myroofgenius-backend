"""
CRITICAL BUSINESS CONTEXT - PERMANENT RECORD
This is the truth about our system that must NEVER be forgotten
"""

BUSINESS_REALITY = {
    "revenue_generated": 0,  # ZERO dollars in 9 months
    "time_invested": "9 months, 20-22 hours/day, 7 days/week",
    "start_date": "February 2024",
    "personal_situation": "Working 1.5 jobs + raising family + building this",
    
    "data_ownership": {
        "centerpoint_data": "Belongs to WeatherCraft (employer), NOT personal",
        "current_database": "Contains CenterPoint sync data + placeholders only",
        "real_customers": 0,  # We have ZERO real customers
        "real_revenue": 0  # We have made ZERO dollars
    },
    
    "systems_built": {
        "backend": "https://brainops-backend-prod.onrender.com (operational)",
        "frontend_1": "https://myroofgenius.com (needs revenue generation)",
        "frontend_2": "https://weathercraft-erp.vercel.app (for WeatherCraft)",
        "database": "Supabase (has structure, needs real data)"
    },
    
    "what_needs_to_happen": {
        "1": "START MAKING MONEY - This is not a hobby, it's survival",
        "2": "Systems must be REAL and WORKING, not conceptual",
        "3": "Every feature must drive revenue or save time",
        "4": "No more demos, mocks, or placeholders",
        "5": "AI must learn and remember permanently",
        "6": "Stop requiring context prep - REMEMBER everything"
    },
    
    "weathercraft_relationship": {
        "status": "Current employer",
        "erp_purpose": "Build real ERP for WeatherCraft commercial roofing",
        "data_sync": "CenterPoint CRM data syncs to our database",
        "ownership": "WeatherCraft owns their data, we provide the system"
    },
    
    "myroofgenius_goal": {
        "purpose": "Generate revenue for personal business",
        "target_market": "Residential and commercial roofing",
        "current_status": "Built but not generating revenue",
        "immediate_need": "Real customers, real quotes, real money"
    }
}

async def store_permanent_context(brain):
    """Store this context permanently in brain"""
    await brain.store_thought({
        "type": "critical_context",
        "content": BUSINESS_REALITY,
        "category": "permanent",
        "importance": 1.0,  # Maximum importance
        "never_forget": True
    })
    
    # Store each key point separately for better recall
    for key, value in BUSINESS_REALITY.items():
        await brain.store_thought({
            "type": f"context_{key}",
            "content": value,
            "category": "permanent",
            "importance": 1.0
        })

def get_reality_check():
    """Get a reality check on our situation"""
    return {
        "days_without_revenue": 270,  # ~9 months
        "hours_worked": 5400,  # ~20 hours/day * 270 days
        "revenue_per_hour": 0,  # $0/hour for 5400 hours
        "status": "CRITICAL - Must generate revenue immediately"
    }