# 🚀 AUREA Complete Deployment Guide - v3.1.142

## 🎯 What's New in v3.1.142
- ✅ **ElevenLabs Voice Integration**: Full voice synthesis with conversational AI voice
- ✅ **Fixed AUREA Web Interface**: Now properly calls API endpoints
- ✅ **Better Error Handling**: Loading screen won't get stuck
- ✅ **Real-time Status Check**: Shows online/offline status

## 📋 Required Environment Variables for Render

### Copy and paste these into Render Dashboard > Environment tab:

```env
# ===== CORE DATABASE (CRITICAL) =====
DATABASE_URL=postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:5432/postgres?sslmode=require
SUPABASE_URL=https://yomagoqdmxszqtdwuhab.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvbWFnb3FkbXhzenF0ZHd1aGFiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk4MzMyNzYsImV4cCI6MjA2NTQwOTI3Nn0.bxlLdnJ1YKYUNlIulSO2E6iM4wyUSrPFtNcONg-vwPY

# ===== AI SERVICES (ALL CONFIGURED) =====
ANTHROPIC_API_KEY=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
OPENAI_API_KEY=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
GEMINI_API_KEY=AIzaSyAdw66Wfnx2RCuxyzuOMOWH9s9Yk5a-s2s
ELEVENLABS_API_KEY=sk_a4be8c327484fa7d24eb94e8b16462827095939269fd6e49
ELEVENLABS_VOICE_ID=elevenlabs-conversational

# ===== INTEGRATIONS =====
GITHUB_TOKEN=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
STRIPE_SECRET_KEY=sk_test_51RHXCuFs5YLnaPiWvnYeslb6WFk6OZJI0VTQsz9uWQP6zJdGXUjpFw0SLRYsVnJEuNFKgfaXfbB8NJ0gwCkHytDQ00kUDul0uF
RENDER_API_KEY=4b6b1a40f7b042f5a04dd1234f3e36c8
RENDER_SERVICE_ID=srv-cja1ipir0cfc73gqbl70

# ===== SECURITY =====
JWT_SECRET_KEY=mPvXTvzgOXi6jHJCAodX1T9bsDpq2O8ggWbtGwx36g4
SECRET_KEY=mPvXTvzgOXi6jHJCAodX1T9bsDpq2O8ggWbtGwx36g4

# ===== FEATURE FLAGS =====
ENABLE_VOICE_SYNTHESIS=true
ENABLE_CONTINUOUS_VOICE=true
ENABLE_INTELLIGENT_GROWTH=true
AI_COPILOT_ENABLED=true
ESTIMATOR_ENABLED=true
AR_MODE_ENABLED=true
SALES_ENABLED=true

# ===== MONITORING =====
PAPERTRAIL_HOST=logs.papertrailapp.com
PAPERTRAIL_PORT=34302

# ===== ENVIRONMENT =====
ENVIRONMENT=production
PYTHONUNBUFFERED=1
PORT=10000
```

## 🚀 Deployment Steps

### 1. Deploy on Render
```bash
# Service: brainops-backend-prod
# Image: mwwoodworth/brainops-backend:v3.1.142
# Status: Docker image pushed and ready
```

### 2. Access AUREA
Once deployed, access AUREA at:
- **Web Interface**: https://brainops-backend-prod.onrender.com/aurea
- **API Status**: https://brainops-backend-prod.onrender.com/api/v1/aurea/status
- **Capabilities**: https://brainops-backend-prod.onrender.com/api/v1/aurea/capabilities

### 3. Test Voice Features
```bash
# Test voice synthesis
curl -X POST https://brainops-backend-prod.onrender.com/api/v1/aurea-simple/command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "Hello AUREA, test your voice",
    "voice_enabled": true
  }'
```

## 📱 Mobile Access
1. Open https://brainops-backend-prod.onrender.com/aurea on your phone
2. Add to home screen for app-like experience
3. Voice commands work with the microphone button
4. Works offline with service worker caching

## 🎤 Voice Commands Examples
- "Show me today's revenue"
- "What are my urgent tasks?"
- "Create a new roofing estimate"
- "Give me a system status update"
- "Draft an email about the Johnson project"

## 🔧 Troubleshooting

### If AUREA keeps reloading:
1. Check browser console for errors
2. Verify API is responding at /api/v1/aurea-simple/status
3. Clear browser cache and reload

### If voice doesn't work:
1. Check ElevenLabs API key is set correctly
2. Verify microphone permissions in browser
3. Check console for voice synthesis errors

## 🎯 What's Working Now
- ✅ AUREA web interface with real API calls
- ✅ Voice synthesis with ElevenLabs
- ✅ All intelligent growth features
- ✅ Role-based access control
- ✅ Claude-powered responses
- ✅ Public health endpoints
- ✅ LangGraph workflows

## 📊 Verify Deployment
After deployment, check:
```bash
# Health check
curl https://brainops-backend-prod.onrender.com/health

# AUREA status
curl https://brainops-backend-prod.onrender.com/api/v1/aurea-simple/status

# Voice synthesis status
curl https://brainops-backend-prod.onrender.com/api/v1/aurea/status
```

## 🚨 Important Notes
- **ElevenLabs**: Your API key is configured and ready
- **Voice ID**: Using "elevenlabs-conversational" for natural speech
- **Character Limit**: Monitor usage in ElevenLabs dashboard
- **Offline Mode**: Service worker provides basic offline functionality

---

**Version**: v3.1.142  
**Status**: READY FOR DEPLOYMENT  
**Docker**: Already pushed to Hub  
**Next Step**: Deploy on Render and test AUREA!