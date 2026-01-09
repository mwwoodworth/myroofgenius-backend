# Vercel Log Drain Configuration for MyRoofGenius

This document intentionally contains **no real secrets**.

## Recommended Settings

### Projects
✅ **All Team Projects**

### Sources (Enable ALL for comprehensive monitoring)
✅ **Static**  
✅ **External**  
✅ **Edge**  
✅ **Build**  
✅ **Function**  
✅ **Firewall**

### Delivery Format
✅ **NDJSON**

### Custom Secret
```
<LOG_DRAIN_SECRET>
```

### Custom Name
```
MyRoofGenius-Production-Logs
```

### Environments
✅ **Production**  
✅ **Pre-production**

### Sampling Rate
**100%** during launch, reduce later if volume is high.

## Endpoint URL
```
https://brainops-backend-prod.onrender.com/api/v1/logs/vercel
```

## Custom Headers
```json
{
  "Authorization": "Bearer <LOG_DRAIN_SECRET>",
  "X-Source": "vercel-log-drain",
  "X-Project": "myroofgenius",
  "Content-Type": "application/json"
}
```

