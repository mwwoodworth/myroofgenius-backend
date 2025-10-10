# Vercel Log Drain Setup Guide

## Quick Setup (Copy & Paste Ready)

### 1. In Vercel Dashboard

Navigate to: **Project Settings → Log Drains → Add Log Drain**

### 2. Fill in the Form

**Endpoint URL:**
```
https://brainops-backend-prod.onrender.com/api/v1/logs/vercel
```

**Projects:**
- [x] All Team Projects

**Sources (CHECK ALL):**
- [x] Static
- [x] External  
- [x] Edge
- [x] Build
- [x] Function
- [x] Firewall

**Delivery Format:**
- [x] NDJSON

**Custom Secret:**
```
myroofgenius_log_drain_secret_2025_02_08_secure
```

**Custom Name:**
```
MyRoofGenius-Production-Logs
```

**Environments:**
- [x] Production
- [x] Pre-production

**Sampling Rate:**
```
100
```

**Custom Headers (paste as JSON):**
```json
{
  "Authorization": "Bearer myroofgenius_log_drain_secret_2025_02_08_secure",
  "X-Source": "vercel-log-drain",
  "X-Project": "myroofgenius",
  "Content-Type": "application/json"
}
```

### 3. Backend Setup

1. **Add the route to your backend** (save as `routes/vercel_logs.py`):
   - File already created at: `/home/mwwoodworth/code/vercel_logs_route.py`

2. **Run the database migration**:
   ```bash
   psql $DATABASE_URL < CREATE_VERCEL_LOGS_TABLE.sql
   ```

3. **Add to main.py**:
   ```python
   from routes import vercel_logs
   app.include_router(vercel_logs.router, prefix="/api/v1", tags=["logs"])
   ```

### 4. Test the Connection

Once configured, Vercel will start sending logs immediately. Test by:

1. Making a request to your frontend
2. Checking backend logs for "📊 Processed X Vercel logs"
3. Viewing stats at: `https://brainops-backend-prod.onrender.com/api/v1/logs/vercel/stats`

## What You'll See

### In Your Backend Logs:
```
📊 Processed 25 Vercel logs
⚠️ Vercel Error: /marketplace/cart - 404 - Not Found
❌ Frontend Error: /api/checkout - TypeError
🔍 Critical 404: /profile
🐌 Slow Request: /tools/calculator took 3500ms
🚨 Build Failed: myroofgenius - Build error
```

### Alert Examples:
- **Build Failures**: Immediate notification
- **404 on Critical Pages**: Tracked for fixing
- **Slow Requests**: Performance monitoring
- **Error Spikes**: Automatic detection

## Benefits

1. **Real-time Visibility**: See errors as they happen
2. **Build Monitoring**: Know immediately if deployments fail
3. **Performance Tracking**: Identify slow pages
4. **Security Monitoring**: Track firewall blocks
5. **User Experience**: Find and fix 404s quickly

## Quick Verification

After setup, run this to verify logs are flowing:

```bash
curl https://brainops-backend-prod.onrender.com/api/v1/logs/vercel/stats
```

You should see log counts increasing.

## Troubleshooting

If logs aren't appearing:

1. **Check Authorization**: Ensure the Bearer token matches exactly
2. **Verify Endpoint**: Must be HTTPS and publicly accessible
3. **Check Sources**: At least one source must be selected
4. **Test Manually**: 
   ```bash
   curl -X POST https://brainops-backend-prod.onrender.com/api/v1/logs/vercel \
     -H "Authorization: Bearer myroofgenius_log_drain_secret_2025_02_08_secure" \
     -H "Content-Type: application/json" \
     -d '{"test": "log"}'
   ```

## Next Steps

1. Set up alerts for critical errors
2. Create dashboard to visualize logs
3. Configure auto-remediation for common issues
4. Set up weekly performance reports

---

**Note**: This log drain will help you catch issues like the Button export error immediately instead of discovering them during testing.