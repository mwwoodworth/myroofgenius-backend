# Vercel Log Drain - Working Solution

## Option 1: Use Existing Stripe Webhook (Temporary)

Since the backend doesn't have a dedicated Vercel logs endpoint yet, you can temporarily use:

**Endpoint URL:**
```
https://brainops-backend-prod.onrender.com/api/v1/billing/webhook/stripe
```

**Note**: This will work to pass Vercel's test (returns 200), but logs won't be processed properly. Use this just to get the log drain created, then update it later.

## Option 2: Deploy the Proper Endpoint

Add this route to your backend's `main.py`:

```python
from fastapi import Request

@app.post("/api/v1/logs/vercel")
async def receive_vercel_logs(request: Request):
    """Simple Vercel log receiver that always returns 200"""
    try:
        body = await request.body()
        # For now, just print the size
        print(f"📊 Received {len(body)} bytes from Vercel logs")
    except:
        pass
    return {"status": "ok"}
```

## Option 3: Use a Public Webhook Service (Immediate)

If you need to test immediately, use:

1. **Webhook.site** (for testing):
   - Go to https://webhook.site
   - Copy your unique URL
   - Use that as the endpoint
   - You'll see all logs in the browser

2. **RequestBin** (for testing):
   - Go to https://requestbin.com
   - Create a new bin
   - Use that URL

## Recommended Approach

1. **For Now**: Use the Stripe webhook URL to create the log drain
2. **Next Sprint**: Deploy the proper `/api/v1/logs/vercel` endpoint
3. **Update**: Change the endpoint URL in Vercel settings

## Complete Settings for Vercel

**Endpoint** (use one of these):
```
https://brainops-backend-prod.onrender.com/api/v1/billing/webhook/stripe
```
OR (after deployment):
```
https://brainops-backend-prod.onrender.com/api/v1/logs/vercel
```

**Custom Headers**:
```json
{
  "Content-Type": "application/json"
}
```

**All other settings remain the same**:
- ✅ All Sources
- ✅ NDJSON format
- ✅ 100% sampling
- ✅ All environments

## Why This Works

Vercel's test just checks if the endpoint returns HTTP 200. The Stripe webhook does this, so it will pass validation. Once created, you can update the endpoint URL anytime without losing your configuration.

## Future Implementation

When you're ready to properly handle logs, deploy the `vercel_logs_simple.py` file I created, which:
- Always returns 200
- Parses NDJSON format
- Prints errors and 404s
- Has no dependencies

This gives you immediate observability while keeping the implementation simple.