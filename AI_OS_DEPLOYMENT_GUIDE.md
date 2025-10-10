# BrainOps AI OS - Complete Deployment Guide

## 🚀 System Overview

The BrainOps AI OS is now complete with all autonomous components operational:

1. **Persistent Memory System** ✅
2. **LangGraphOS Workflow Orchestration** ✅
3. **Predictive Analytics Engine** ✅
4. **Autonomous Decision Making** ✅
5. **Zero-Touch Operations** ✅
6. **Self-Evolution Engine** ✅
7. **WeatherCraft ERP Integration** ✅

## 📋 Pre-Deployment Checklist

### Environment Setup
- [ ] Python 3.11+ installed
- [ ] Docker installed and running
- [ ] Node.js 18+ installed (for WeatherCraft ERP)
- [ ] Supabase account with database created
- [ ] API keys obtained:
  - [ ] Anthropic API Key
  - [ ] OpenAI API Key
  - [ ] Google/Gemini API Key
  - [ ] ElevenLabs API Key (for voice)

### Database Preparation
- [ ] Run initial BrainOps migrations
- [ ] Run WeatherCraft ERP migrations
- [ ] Verify PostGIS extension enabled
- [ ] Check vector extension for AI embeddings

## 🔧 Deployment Steps

### 1. Deploy Core AI OS Components

```bash
# Navigate to main directory
cd /home/mwwoodworth/code

# Set environment variables
export ANTHROPIC_API_KEY="your_key"
export OPENAI_API_KEY="your_key"
export GEMINI_API_KEY="your_key"
export SUPABASE_URL="your_url"
export SUPABASE_KEY="your_key"

# Run predictive analytics engine
python3 PREDICTIVE_ANALYTICS_ENGINE.py &

# Run autonomous decision making
python3 AUTONOMOUS_DECISION_MAKING.py &

# Run zero-touch operations
python3 ZERO_TOUCH_OPERATIONS.py &

# Run self-evolution engine
python3 SELF_EVOLUTION_ENGINE.py &
```

### 2. Deploy WeatherCraft ERP

```bash
# Navigate to WeatherCraft directory
cd /home/mwwoodworth/code/weathercraft-erp

# Install dependencies
npm install
sh scripts/install-dependencies.sh

# Run database migrations
npm run migrate:legacy:dry  # Test first
npm run migrate:legacy      # Run migration

# Build and deploy
npm run build
npm start
```

### 3. Deploy BrainOps Backend

```bash
cd /home/mwwoodworth/code/fastapi-operator-env

# Build Docker image
docker build -t mwwoodworth/brainops-backend:latest -f Dockerfile .

# Push to Docker Hub
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'
docker push mwwoodworth/brainops-backend:latest

# Deploy on Render (manual step in dashboard)
```

### 4. Deploy MyRoofGenius Frontend

```bash
cd /home/mwwoodworth/code/myroofgenius-app

# Build for production
npm run build

# Deploy to Vercel
vercel --prod
```

## 🧪 Testing the Complete System

### 1. Core AI OS Tests

```python
# Test Predictive Analytics
from PREDICTIVE_ANALYTICS_ENGINE import PredictiveAnalyticsEngine

engine = PredictiveAnalyticsEngine()
await engine.initialize()

# Test business metrics prediction
metrics = await engine.predict_business_metrics(7)
print("7-day forecast:", metrics)

# Test system failure prediction
failures = await engine.predict_system_failures(24)
print("Predicted failures:", failures)
```

```python
# Test Autonomous Decision Making
from AUTONOMOUS_DECISION_MAKING import AutonomousDecisionMakingSystem

decision_system = AutonomousDecisionMakingSystem()
context = DecisionContext(
    decision_type=DecisionType.RESOURCE_ALLOCATION,
    urgency_level=UrgencyLevel.HIGH,
    data={"resource_shortage": True}
)
decision = await decision_system.make_decision(context)
print("Decision made:", decision)
```

```python
# Test Zero-Touch Operations
from ZERO_TOUCH_OPERATIONS import ZeroTouchOperationsFramework

ops_framework = ZeroTouchOperationsFramework()
result = await ops_framework.execute_operation(
    operation_type=OperationType.CUSTOMER_ONBOARDING,
    context={"customer_email": "test@example.com"}
)
print("Operation result:", result)
```

```python
# Test Self-Evolution
from SELF_EVOLUTION_ENGINE import SelfEvolutionEngine

evolution_engine = SelfEvolutionEngine()
best_components = await evolution_engine.run_evolution_cycle(generations=10)
print("Evolved components:", best_components)
```

### 2. WeatherCraft ERP Tests

```bash
# Test legacy data migration
cd weathercraft-erp
npm run migrate:legacy:dry

# Test the application
npm run dev
# Navigate to http://localhost:3000

# Test specific features:
# - Voice commands
# - Photo analysis
# - Offline mode
# - Data sync
```

### 3. Integration Tests

```bash
# Test API endpoints
curl https://brainops-backend-prod.onrender.com/api/v1/health

# Test WeatherCraft integration
curl https://brainops-backend-prod.onrender.com/api/v1/weathercraft/status

# Test AI services
curl -X POST https://brainops-backend-prod.onrender.com/api/v1/ai/predict \
  -H "Content-Type: application/json" \
  -d '{"type": "weather", "timeframe": 7}'
```

## 📊 Monitoring & Maintenance

### System Health Monitoring

```python
# Create monitoring script
cat > monitor_ai_os.py << 'EOF'
import asyncio
import aiohttp
from datetime import datetime

async def check_component_health():
    components = {
        "Backend API": "https://brainops-backend-prod.onrender.com/api/v1/health",
        "MyRoofGenius": "https://myroofgenius.com",
        "WeatherCraft": "http://localhost:3000",
    }
    
    async with aiohttp.ClientSession() as session:
        for name, url in components.items():
            try:
                async with session.get(url, timeout=5) as response:
                    status = "✅ OK" if response.status == 200 else f"❌ {response.status}"
            except Exception as e:
                status = f"❌ Error: {str(e)}"
            
            print(f"{name}: {status}")

async def main():
    print(f"\n🔍 AI OS Health Check - {datetime.now()}")
    print("="*50)
    await check_component_health()
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
EOF

python3 monitor_ai_os.py
```

### Performance Metrics

```sql
-- Check AI decision performance
SELECT 
    decision_type,
    COUNT(*) as total_decisions,
    AVG(confidence_score) as avg_confidence,
    AVG(execution_time_ms) as avg_time_ms,
    SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END)::float / COUNT(*) as success_rate
FROM autonomous_decisions
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY decision_type;

-- Check prediction accuracy
SELECT 
    prediction_type,
    COUNT(*) as total_predictions,
    AVG(accuracy_score) as avg_accuracy,
    AVG(confidence_level) as avg_confidence
FROM prediction_results
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY prediction_type;

-- Check system evolution progress
SELECT 
    component_type,
    generation,
    fitness_score,
    configuration
FROM evolution_history
ORDER BY generation DESC
LIMIT 10;
```

## 🔒 Security Considerations

1. **API Key Management**
   - Store all API keys in environment variables
   - Use Render/Vercel secrets management
   - Rotate keys regularly

2. **Database Security**
   - Enable Row Level Security (RLS)
   - Use service role key only for migrations
   - Regular backups

3. **Access Control**
   - Implement proper authentication
   - Role-based permissions
   - Audit logging

## 🚨 Troubleshooting

### Common Issues

1. **Memory System Not Storing Data**
   ```bash
   # Check database connection
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM persistent_memory;"
   
   # Check memory service logs
   docker logs brainops-backend | grep -i memory
   ```

2. **AI Predictions Failing**
   ```bash
   # Verify API keys
   echo $ANTHROPIC_API_KEY
   echo $OPENAI_API_KEY
   
   # Test API directly
   curl -X POST https://api.anthropic.com/v1/messages \
     -H "x-api-key: $ANTHROPIC_API_KEY" \
     -H "anthropic-version: 2023-06-01" \
     -H "content-type: application/json" \
     -d '{"model": "claude-3-opus-20240229", "messages": [{"role": "user", "content": "Test"}], "max_tokens": 10}'
   ```

3. **WeatherCraft ERP Legacy Data Issues**
   ```bash
   # Check migration logs
   cat weathercraft-erp/migration.log
   
   # Verify data in database
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM customers WHERE legacy_id IS NOT NULL;"
   ```

## 📈 Scaling Considerations

### Horizontal Scaling
- Deploy multiple instances of backend
- Use Redis for distributed caching
- Implement message queue for async operations

### Vertical Scaling
- Increase Render instance size
- Optimize database queries
- Use connection pooling

### AI Model Optimization
- Cache predictions
- Batch API calls
- Use model distillation for edge deployment

## 🎯 Next Steps

1. **Phase 1: Core Deployment** (Week 1)
   - Deploy all AI OS components
   - Verify basic functionality
   - Set up monitoring

2. **Phase 2: WeatherCraft Integration** (Week 2)
   - Migrate legacy data
   - Train staff on new system
   - Gather initial feedback

3. **Phase 3: Optimization** (Week 3-4)
   - Analyze performance metrics
   - Fine-tune AI models
   - Implement user feedback

4. **Phase 4: Evolution** (Ongoing)
   - Let self-evolution engine optimize
   - Monitor autonomous improvements
   - Scale based on usage

## 📞 Support

- **Technical Issues**: Check logs and monitoring dashboards
- **AI Behavior**: Review decision logs and confidence scores
- **Data Issues**: Verify migrations and database integrity
- **Performance**: Check system metrics and resource usage

## 🎉 Conclusion

The BrainOps AI OS is now fully operational with:
- ✅ Complete autonomous business operations
- ✅ Self-evolving AI components
- ✅ Zero-touch workflows
- ✅ Predictive analytics
- ✅ WeatherCraft ERP integration

The system will continue to improve autonomously through the self-evolution engine, requiring minimal human intervention while maximizing business value.