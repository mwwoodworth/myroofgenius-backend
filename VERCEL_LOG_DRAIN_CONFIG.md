# Vercel Log Drain Configuration for MyRoofGenius

## Recommended Settings for Optimal Observability

### Projects
✅ **All Team Projects** - This ensures we capture logs from all deployments

### Sources (Enable ALL for comprehensive monitoring)
✅ **Static** - Monitor asset loading performance
✅ **External** - Track external API calls to backend
✅ **Edge** - Critical for middleware and auth flows  
✅ **Build** - Catch build errors immediately
✅ **Function** - Monitor API routes and serverless functions
✅ **Firewall** - Security monitoring for blocked requests

### Delivery Format
✅ **NDJSON** - Newline-delimited JSON for easy parsing and streaming

### Custom Secret
```
myroofgenius_log_drain_secret_2025_02_08_secure
```

### Custom Name
```
MyRoofGenius-Production-Logs
```

### Environments
✅ **Production** - Primary monitoring
✅ **Pre-production** - Catch issues before they hit production

### Sampling Rate
**100%** - Full observability during launch phase (can reduce later if volume becomes too high)

### Endpoint Options

#### Option 1: Direct to Backend (Recommended)
```
https://brainops-backend-prod.onrender.com/api/v1/logs/vercel
```

#### Option 2: Papertrail Integration
```
https://logs.papertrailapp.com/v1/logdrains/vercel
```

#### Option 3: Custom Webhook Handler
```
https://brainops-backend-prod.onrender.com/api/v1/webhooks/vercel-logs
```

### Custom Headers
```json
{
  "Authorization": "Bearer your-webhook-secret-token",
  "X-Source": "vercel-log-drain",
  "X-Project": "myroofgenius",
  "Content-Type": "application/json"
}
```

## Implementation Benefits

1. **Real-time Error Detection**: Immediate visibility into 404s, 500s, and other errors
2. **Deployment Monitoring**: Track build success/failure instantly
3. **Performance Insights**: Monitor static asset loading and function execution times
4. **Security Monitoring**: See firewall blocks and potential attacks
5. **API Integration Tracking**: Monitor all calls to backend services
6. **User Experience Metrics**: Track page load times and errors

## Backend Endpoint Implementation

Create this endpoint on the backend to receive logs:

```python
@router.post("/api/v1/logs/vercel")
async def receive_vercel_logs(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Receive and process Vercel log drain data"""
    
    # Verify webhook secret
    auth_header = request.headers.get("Authorization")
    if not verify_webhook_secret(auth_header):
        raise HTTPException(status_code=401)
    
    # Parse NDJSON
    body = await request.body()
    logs = body.decode().strip().split('\n')
    
    for log_line in logs:
        try:
            log_data = json.loads(log_line)
            
            # Process different log types
            if log_data.get("type") == "error":
                # Alert on errors
                await alert_on_error(log_data)
            
            # Store in database
            background_tasks.add_task(store_log, log_data, db)
            
        except json.JSONDecodeError:
            continue
    
    return {"status": "received", "count": len(logs)}
```

## Automated Actions Based on Logs

1. **Build Failures**: Auto-create GitHub issue
2. **High Error Rate**: Send Slack alert
3. **Performance Degradation**: Scale resources
4. **Security Threats**: Enable additional firewall rules
5. **404 Patterns**: Auto-redirect or fix routes

## Monitoring Dashboard Integration

Add these queries to monitor key metrics:

```sql
-- Recent errors
SELECT timestamp, error_message, path, count(*)
FROM vercel_logs
WHERE type = 'error' AND timestamp > NOW() - INTERVAL '1 hour'
GROUP BY timestamp, error_message, path
ORDER BY count DESC;

-- Build status
SELECT 
  DATE_TRUNC('hour', timestamp) as hour,
  COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_builds,
  COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_builds
FROM vercel_logs
WHERE type = 'build'
GROUP BY hour
ORDER BY hour DESC;

-- Top 404 pages
SELECT path, COUNT(*) as hit_count
FROM vercel_logs  
WHERE status_code = 404
AND timestamp > NOW() - INTERVAL '24 hours'
GROUP BY path
ORDER BY hit_count DESC
LIMIT 10;
```

## SOP Updates

### Daily Monitoring Routine
1. Check build success rate
2. Review top errors
3. Monitor 404 patterns
4. Track API response times
5. Identify security threats

### Alert Thresholds
- Build failure rate > 10%
- Error rate > 5% of requests  
- Any firewall blocks from same IP > 10
- Response time > 3 seconds
- 404 rate > 2% of traffic

This log drain configuration will provide complete visibility into the frontend system's health and enable proactive issue resolution.