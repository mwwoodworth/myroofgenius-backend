# Vercel Log Drain Secrets - CRITICAL

## Production Secrets

### Log Drain Authentication Secret
```
OePGf0hbhwwkuseaXgQPJ8Sv
```

### Verification Header
```
x-vercel-verify: d394968241b1d8d5870c2670f54fc1a2a9bdf8eb
```

### Previous Webhook Secret (deprecated)
```
myroofgenius_log_drain_secret_2025_02_08_secure
```

## Configuration

### Production Log Drain URL
```
https://brainops-backend-prod.onrender.com/api/v1/logs/vercel
```

### Headers to Send
```
Authorization: Bearer OePGf0hbhwwkuseaXgQPJ8Sv
```

## Implementation Status

- ✅ Endpoint created at `/api/v1/logs/vercel`
- ✅ Verification header added to all endpoints
- ✅ POST endpoint accepts NDJSON format
- ✅ GET endpoint provides health check
- ✅ HEAD endpoint supports validation
- ✅ OPTIONS endpoint for CORS
- ✅ All logs stored in persistent memory
- ✅ Error pattern recognition
- ✅ 404 tracking for missing routes
- ✅ Performance monitoring
- ✅ Build status tracking
- ✅ Security event monitoring

## Available Endpoints

1. **Main Log Receiver**
   - POST `/api/v1/logs/vercel`
   - Accepts NDJSON format from Vercel
   - Stores all logs in persistent memory

2. **Health Check**
   - GET `/api/v1/logs/vercel`
   - Returns status with verification header

3. **Statistics**
   - GET `/api/v1/logs/vercel/stats?hours=24`
   - Returns error counts, status codes, 404 paths

4. **Recent Logs**
   - GET `/api/v1/logs/vercel/recent?limit=50&level=error`
   - Returns recent logs filtered by level

5. **Test Endpoint**
   - POST `/api/v1/logs/vercel/test`
   - For testing log processing

## Memory Storage

All Vercel logs are stored in the persistent memory system with:
- Memory type: `vercel_log`
- Owner: `system`
- Tags: Include source, type, level
- Meta data: Full log context including timestamps, paths, status codes, etc.

## AI Learning Features

1. **Error Analysis**: Automatic pattern recognition and suggestions
2. **404 Tracking**: Identifies missing routes for implementation
3. **Performance Monitoring**: Tracks slow requests (>1s)
4. **Build Tracking**: Monitors build success rates
5. **Security Events**: Tracks firewall and blocked requests

## Deployment

Currently deployed in v3.1.221 with all features active.