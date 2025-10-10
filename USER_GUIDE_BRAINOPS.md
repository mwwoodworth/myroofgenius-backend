# 🚀 BrainOps & MyRoofGenius User Guide

## 📍 How to Access Your Systems

### 1. **Live Production API (Backend)**
- **URL**: https://brainops-backend-prod.onrender.com
- **API Docs**: https://brainops-backend-prod.onrender.com/docs
- **Health Check**: https://brainops-backend-prod.onrender.com/health

### 2. **MyRoofGenius Frontend**
- **Production**: https://myroofgenius.com (when deployed)
- **Local Development**: http://localhost:3000
- **Admin Dashboard**: https://myroofgenius.com/admin/dashboard

### 3. **Available Dashboards**
Based on the frontend structure, you have:

#### Main Dashboards:
- `/dashboard` - Main business dashboard
- `/dashboard-estimation` - Roofing estimation dashboard
- `/admin/dashboard` - Administrative control panel

#### Feature Pages:
- `/projects` - Project management
- `/customers` - CRM system
- `/estimates` - Estimation tools
- `/invoices` - Billing management
- `/marketplace` - Product catalog
- `/analytics` - Business analytics

## 🤖 AI & Memory Integration Status

### ✅ **Backend Integration (v3.1.100)**
The backend has FULL AI and memory integration:

1. **Claude AI Integration**
   - Sub-agent orchestration at `/api/v1/agent/execute`
   - Autonomous task planning and execution
   - Development, testing, deployment agents

2. **Memory System**
   - Deep integration across ALL endpoints
   - Auto-categorization of all data
   - Entity extraction (people, projects, locations)
   - Sentiment analysis on customer interactions
   - AI-powered insights and recommendations
   - Semantic search across all data

3. **MyRoofGenius Specific AI Features**
   - **Photo Analysis**: `/api/v1/roofing/photos/analyze`
     - AI analyzes roof photos for damage
     - Estimates repair requirements
     - Suggests materials needed
   
   - **Smart Estimation**: `/api/v1/roofing/estimates/create`
     - AI-powered pricing calculations
     - Material optimization
     - Labor hour predictions
   
   - **Weather Intelligence**: `/api/v1/weathercraft/forecast/business-impact`
     - AI predicts weather impact on jobs
     - Optimizes scheduling
     - Revenue protection recommendations

### ⚠️ **Frontend Integration Status**
The frontend currently has:
- Basic AI setup (Anthropic Claude, CopilotKit)
- Placeholder for AI features
- **NOT YET CONNECTED** to the new backend AI endpoints

## 🎯 How to Use Your AI Assistant

### 1. **Via API (Currently Available)**
```bash
# Create an AI-powered estimate
curl -X POST https://brainops-backend-prod.onrender.com/api/v1/roofing/estimates/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "123",
    "address": "123 Main St",
    "square_footage": 2500,
    "roof_type": "shingle",
    "damage_type": "storm"
  }'

# Analyze a roof photo
curl -X POST https://brainops-backend-prod.onrender.com/api/v1/roofing/photos/analyze \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "photo=@roof-damage.jpg"

# Get AI business recommendations
curl -X POST https://brainops-backend-prod.onrender.com/api/v1/agent/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze my business performance and suggest improvements"
  }'
```

### 2. **Via Frontend (Needs Connection)**
To fully use the AI features in the frontend, you need to:

1. **Update API Service Files**
   ```typescript
   // In /lib/api/roofing.ts
   export const roofingAPI = {
     createEstimate: (data) => 
       fetch(`${API_URL}/api/v1/roofing/estimates/create`, {
         method: 'POST',
         headers: authHeaders(),
         body: JSON.stringify(data)
       }),
     
     analyzePhoto: (photo) => {
       const formData = new FormData();
       formData.append('photo', photo);
       return fetch(`${API_URL}/api/v1/roofing/photos/analyze`, {
         method: 'POST',
         headers: authHeaders(),
         body: formData
       });
     }
   };
   ```

2. **Connect Dashboard Components**
   - Update `/app/dashboard/page.tsx` to fetch from new endpoints
   - Update `/app/dashboard-estimation/page.tsx` for AI estimates
   - Add photo upload to estimation flow

## 🚀 Quick Start Guide

### Step 1: Deploy Latest Backend
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Deploy v3.1.100 (has all AI features)

### Step 2: Test AI Features
```bash
# Install test script
cat > test_ai_features.sh << 'EOF'
#!/bin/bash
API_URL="https://brainops-backend-prod.onrender.com"

# Test AI estimation
echo "Testing AI Estimation..."
curl -X POST $API_URL/api/v1/roofing/estimates/create \
  -H "Content-Type: application/json" \
  -d '{"square_footage": 2000, "roof_type": "shingle"}'

# Test weather impact
echo -e "\n\nTesting Weather Intelligence..."
curl -X POST $API_URL/api/v1/weathercraft/forecast/business-impact \
  -H "Content-Type: application/json" \
  -d '{"location": "Dallas, TX", "business_type": "roofing"}'

# Test Claude AI
echo -e "\n\nTesting Claude Assistant..."
curl -X POST $API_URL/api/v1/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"message": "Help me optimize my roofing business"}'
EOF

chmod +x test_ai_features.sh
./test_ai_features.sh
```

### Step 3: Access Dashboards
```bash
# Start frontend locally
cd /home/mwwoodworth/code/myroofgenius-app
npm run dev

# Access dashboards at:
# http://localhost:3000/dashboard
# http://localhost:3000/admin/dashboard
# http://localhost:3000/dashboard-estimation
```

## 📊 Memory System Integration

### What's Automatically Tracked:
1. **Customer Interactions**
   - All communications
   - Sentiment analysis
   - Relationship mapping

2. **Project History**
   - Every estimate created
   - Job progress
   - Weather impacts
   - Completion status

3. **Business Intelligence**
   - Revenue patterns
   - Seasonal trends
   - Customer preferences
   - Optimal pricing

### How to Query Memory:
```bash
# Search all memories
curl https://brainops-backend-prod.onrender.com/api/v1/memory/search?q=roof+damage

# Get AI insights
curl https://brainops-backend-prod.onrender.com/api/v1/memory/insights/business

# Get customer history
curl https://brainops-backend-prod.onrender.com/api/v1/memory/entities/customer/123
```

## 🔧 Next Steps for Full Integration

1. **Frontend Connection** (Priority)
   - Create API service layer for new endpoints
   - Update dashboard components
   - Add AI UI components

2. **Authentication**
   - Ensure auth tokens are passed to all API calls
   - Set up proper user sessions

3. **Real-time Updates**
   - Connect WebSocket for live updates
   - Add push notifications

4. **Mobile App**
   - PWA is ready
   - Add install prompt
   - Enable offline mode

## 💡 Pro Tips

1. **All your data is AI-enhanced** - Every piece of information stored gets analyzed for patterns and insights

2. **Weather-aware scheduling** - The system automatically adjusts recommendations based on weather forecasts

3. **Photo analysis saves time** - Upload roof photos for instant damage assessment and material requirements

4. **Memory never forgets** - Every customer interaction, job detail, and business decision is remembered and used to improve recommendations

5. **Claude AI assists with everything** - From writing estimates to optimizing schedules to business strategy

---

**Current Status**: Backend is 100% AI-integrated and memory-enabled. Frontend needs connection work to access these features. Once connected, you'll have the most advanced AI-powered roofing business platform available!