# Vercel Log Drain Setup Guide

This guide is safe to commit. It contains **no real secrets**.

## 1) In Vercel Dashboard

Navigate to: **Project Settings → Log Drains → Add Log Drain**

## 2) Configure Log Drain

**Endpoint URL:**
```
https://brainops-backend-prod.onrender.com/api/v1/logs/vercel
```

**Projects:**
- [x] All Team Projects

**Sources (recommended):**
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
<LOG_DRAIN_SECRET>
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
  "Authorization": "Bearer <LOG_DRAIN_SECRET>",
  "X-Source": "vercel-log-drain",
  "X-Project": "myroofgenius",
  "Content-Type": "application/json"
}
```

## 3) Verify

- Health: `https://brainops-backend-prod.onrender.com/api/v1/logs/vercel`
- Stats: `https://brainops-backend-prod.onrender.com/api/v1/logs/vercel/stats?hours=24`

