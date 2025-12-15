# BrainOps System Architecture - Master Documentation

## Current Production Architecture

### Backend (Single Source of Truth)
- **URL**: https://brainops-backend-prod.onrender.com
- **Service ID**: srv-cja1ipir0cfc73gqbl70
- **Database**: Supabase PostgreSQL
- **Repository**: github.com/mwwoodworth/myroofgenius-backend

### Frontends
1. **MyRoofGenius**: https://myroofgenius.com (Vercel)
2. **WeatherCraft ERP**: https://weathercraft-erp.vercel.app (Vercel)

### Database
- **Provider**: Supabase
- **URL**: postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres
- **Project**: yomagoqdmxszqtdwuhab

## Environment Variables Master Table

| Category | Variable | Service | Status |
|----------|----------|---------|--------|
| **Core** |
| | DATABASE_URL | All | ✅ Active |
| | SUPABASE_URL | All | ✅ Active |
| | SUPABASE_SERVICE_ROLE_KEY | Backend | ✅ Active |
| | REDIS_URL | Backend | ⚠️ Local only |
| **AI/ML** |
| | OPENAI_API_KEY | Backend | ✅ Active |
| | ANTHROPIC_API_KEY | Backend | ✅ Active |
| | CLAUDE_API_KEY | Backend | ✅ Active |
| | GEMINI_API_KEY | Backend | ✅ Active |
| | PERPLEXITY_API_KEY | Backend | ✅ Active |
| **Communications** |
| | SENDGRID_API_KEY | Backend | ✅ Active |
| | TWILIO_ACCOUNT_SID | Backend | ❌ Not configured |
| | SLACK_WEBHOOK_URL | Backend | ✅ Active |
| | CONVERTKIT_API_KEY | Backend | ✅ Active |
| **Payments** |
| | STRIPE_SECRET_KEY | Backend | ✅ Active |
| | STRIPE_WEBHOOK_SECRET | Backend | ✅ Active |
| **Integrations** |
| | CENTERPOINT_API_KEY | Backend | ✅ Active |
| | CLICKUP_API_KEY | Backend | ✅ Active |
| | NOTION_API_KEY | Backend | ✅ Active |
| | AIRTABLE_API_KEY | Backend | ✅ Active |
| | GITHUB_TOKEN | Backend | ✅ Active |
| **Monitoring** |
| | SENTRY_DSN | All | ✅ Active |
| | RENDER_API_KEY | Backend | ✅ Active |

## System Components Status

### ✅ Operational
- FastAPI Backend on Render
- Supabase Database
- MyRoofGenius Frontend
- WeatherCraft ERP Frontend
- Stripe Integration
- SendGrid Email
- Slack Notifications
- Sentry Monitoring

### ⚠️ Partially Operational
- Redis (local only, needs cloud deployment)
- AI Task OS (built but not integrated)
- LangGraph Orchestration (installed but not active)

### ❌ Not Operational
- Twilio SMS
- Persistent Memory System (needs Supabase integration)
- AI Agent Network (needs implementation)

## Data Flow Architecture

```
User Request → Vercel Frontend → Render Backend → Supabase DB
                                        ↓
                              LangGraph Orchestration
                                        ↓
                          Specialized AI Agents (50+)
                                        ↓
                              Persistent Memory Layer
                                        ↓
                              Response Generation
```

## AI Agent Categories

1. **Revenue Agents**: Lead capture, pricing, conversion
2. **Operations Agents**: Scheduling, resource management
3. **Technical Agents**: Code generation, debugging, deployment
4. **Customer Agents**: Support, success, retention
5. **Financial Agents**: Invoicing, payments, reporting
6. **Marketing Agents**: Content, SEO, campaigns
7. **Security Agents**: Threat detection, compliance
8. **Industry Agents**: Roofing-specific, weather analysis

## Next Implementation Priority

1. Connect Redis to cloud (Upstash or Redis Cloud)
2. Implement Supabase persistent memory
3. Activate LangGraph orchestration
4. Deploy specialized AI agents
5. Enable real-time WebSocket connections
6. Complete Twilio integration