# 🔐 Stripe Key Rotation - Autonomous Strategy

## The Challenge
Stripe's rolling API keys expire after 7 days for security. We need an autonomous solution.

## Solution Options

### Option 1: Use Permanent Restricted Keys (RECOMMENDED)
Instead of rolling keys, create a **Restricted API Key** with specific permissions:

1. Go to https://dashboard.stripe.com/apikeys
2. Click "Create restricted key"
3. Name it: "MyRoofGenius Production"
4. Grant these permissions:
   - **Customers**: Write
   - **Charges**: Write
   - **Payment Intents**: Write
   - **Checkout Sessions**: Write
   - **Subscriptions**: Write
   - **Products**: Read
   - **Prices**: Read
   - **Webhooks**: Write
   - **Billing Portal**: Write

This key **never expires** and has only the permissions needed.

### Option 2: Environment Variable Rotation
Store keys in Render environment variables and update weekly:

```python
# In your backend code
import os
from datetime import datetime, timedelta

class StripeKeyManager:
    def __init__(self):
        # Try multiple keys in order
        self.keys = [
            os.getenv("STRIPE_SECRET_KEY_PRIMARY"),
            os.getenv("STRIPE_SECRET_KEY_SECONDARY"),
            os.getenv("STRIPE_SECRET_KEY_FALLBACK")
        ]
    
    def get_valid_key(self):
        """Try each key until one works"""
        import stripe
        
        for key in self.keys:
            if not key:
                continue
            try:
                stripe.api_key = key
                stripe.Account.retrieve()
                return key
            except:
                continue
        
        raise Exception("No valid Stripe key found")
```

### Option 3: Vault/Secrets Manager (Most Secure)
Use a secrets management service:

1. **AWS Secrets Manager**
```python
import boto3
import json

def get_stripe_key():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='stripe-api-key')
    return json.loads(response['SecretString'])['api_key']
```

2. **HashiCorp Vault**
```python
import hvac

def get_stripe_key():
    client = hvac.Client(url='https://vault.myroofgenius.com')
    response = client.secrets.kv.v2.read_secret_version(path='stripe/keys')
    return response['data']['data']['secret_key']
```

3. **Render's Native Secrets**
```python
# Store in Render dashboard as encrypted secret
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY_ENCRYPTED")
```

## Immediate Implementation (5 minutes)

### Step 1: Create Restricted Key Now
```bash
# Go to Stripe Dashboard
open https://dashboard.stripe.com/apikeys

# Click "Create restricted key"
# Set permissions listed above
# Copy the key (starts with rk_live_)
```

### Step 2: Update Backend
```python
# /home/mwwoodworth/code/fastapi-operator-env/routes/stripe_automation.py

import os
import stripe
from datetime import datetime

# Fallback chain of keys
STRIPE_KEYS = [
    os.getenv("STRIPE_RESTRICTED_KEY"),  # Permanent restricted key
    os.getenv("STRIPE_SECRET_KEY"),       # Rolling key (7 days)
    os.getenv("STRIPE_BACKUP_KEY")        # Emergency backup
]

def initialize_stripe():
    """Initialize Stripe with first working key"""
    for key in STRIPE_KEYS:
        if not key:
            continue
        try:
            stripe.api_key = key
            account = stripe.Account.retrieve()
            print(f"✅ Stripe initialized with key ending in ...{key[-4:]}")
            return True
        except stripe.error.AuthenticationError:
            continue
    
    # Send alert if all keys fail
    send_alert("All Stripe keys failed - immediate action required")
    return False

# Initialize on startup
initialize_stripe()
```

### Step 3: Set Up Key Rotation Reminder
```python
# Add to your backend startup
from datetime import datetime, timedelta

def check_key_expiry():
    """Check if keys are expiring soon"""
    key_created = datetime(2025, 8, 19)  # Today
    days_until_expiry = 7 - (datetime.now() - key_created).days
    
    if days_until_expiry <= 2:
        send_notification(
            f"⚠️ Stripe key expires in {days_until_expiry} days. "
            f"Update at https://dashboard.stripe.com/apikeys"
        )
    
    return days_until_expiry

# Run daily
schedule.every().day.at("09:00").do(check_key_expiry)
```

## Automation Script for Key Rotation

```python
#!/usr/bin/env python3
# /home/mwwoodworth/code/rotate_stripe_keys.py

import os
import stripe
import requests
from datetime import datetime

def rotate_stripe_key():
    """Automatically rotate Stripe key via API"""
    
    # Note: Stripe doesn't have an API for key rotation
    # This would need to be done via webhook from Stripe
    # or manual update with notification
    
    # For now, send reminder
    webhook_url = "YOUR_SLACK_WEBHOOK"
    
    message = {
        "text": "🔐 Stripe Key Rotation Required",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Action Required*\n"
                           f"Stripe key expires tomorrow.\n"
                           f"1. Go to <https://dashboard.stripe.com/apikeys|Stripe Dashboard>\n"
                           f"2. Create new restricted key\n"
                           f"3. Update in <https://dashboard.render.com|Render Environment>"
                }
            }
        ]
    }
    
    requests.post(webhook_url, json=message)

# Schedule this to run every 5 days
if __name__ == "__main__":
    rotate_stripe_key()
```

## The Best Solution: Restricted Keys

**Why Restricted Keys are Best:**
1. **Never expire** - No rotation needed
2. **Minimal permissions** - More secure
3. **Audit trail** - Track usage
4. **Multiple keys** - Can have backup keys
5. **Immediate revocation** - If compromised

**How to Set It Up Right Now:**
1. Go to https://dashboard.stripe.com/apikeys
2. Create a restricted key with only needed permissions
3. Replace the current key in Render
4. Done - it works forever

## Backup Strategy

Always have 3 keys configured:
1. **Primary**: Restricted key (permanent)
2. **Secondary**: Rolling key (7 days)
3. **Emergency**: Test mode key (fallback)

```python
# Environment variables in Render
STRIPE_RESTRICTED_KEY=rk_live_...  # Permanent
STRIPE_SECRET_KEY=sk_live_...      # Rolling (current)
STRIPE_TEST_KEY=sk_test_...        # Emergency fallback
```

## Monitoring & Alerts

Add monitoring to detect key issues:

```python
@app.on_event("startup")
async def startup_event():
    """Check Stripe keys on startup"""
    if not initialize_stripe():
        # Send critical alert
        send_sms("+1234567890", "Stripe keys failed - revenue system down!")
        send_email("admin@myroofgenius.com", "CRITICAL: Stripe Authentication Failed")
```

---

**Recommended Action**: Create a restricted key now - it takes 2 minutes and solves the problem permanently.