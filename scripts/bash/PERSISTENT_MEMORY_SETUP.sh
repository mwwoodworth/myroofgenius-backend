#!/bin/bash

# PERSISTENT MEMORY SYSTEM SETUP
# This keeps AI context across sessions

echo "🧠 Setting up Persistent Memory System..."

# 1. Create context directory
mkdir -p ~/.ai_context
mkdir -p ~/code/.context

# 2. Create context bridge Python script
cat > ~/code/context_bridge.py << 'EOF'
import json
import os
from datetime import datetime
from supabase import create_client

class ContextBridge:
    def __init__(self):
        # Use existing Supabase connection
        self.supabase = create_client(
            "https://yomagoqdmxszqtdwuhab.supabase.co",
            "<JWT_REDACTED>"
        )
        self.local_file = os.path.expanduser('~/.ai_context/current.json')
        
    def save_context(self, key, value):
        # Load existing context
        context = {}
        if os.path.exists(self.local_file):
            with open(self.local_file, 'r') as f:
                context = json.load(f)
        
        # Update context
        context[key] = {
            'value': value,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Save locally
        os.makedirs(os.path.dirname(self.local_file), exist_ok=True)
        with open(self.local_file, 'w') as f:
            json.dump(context, f, indent=2)
        
        # Sync to Supabase
        try:
            self.supabase.table('ai_memory').upsert({
                'id': f'context_{key}',
                'key': key,
                'value': value,
                'updated_at': datetime.utcnow().isoformat()
            }).execute()
            return True
        except Exception as e:
            print(f"Supabase sync failed: {e}")
            return False
    
    def get_context(self, key=None):
        # Try local first
        if os.path.exists(self.local_file):
            with open(self.local_file, 'r') as f:
                context = json.load(f)
                if key:
                    return context.get(key, {}).get('value')
                return context
        
        # Fallback to Supabase
        try:
            if key:
                result = self.supabase.table('ai_memory').select('*').eq('key', key).execute()
                return result.data[0]['value'] if result.data else None
            else:
                result = self.supabase.table('ai_memory').select('*').execute()
                return {item['key']: item['value'] for item in result.data}
        except:
            return None
    
    def get_status(self):
        return {
            'backend': 'v4.35 operational',
            'myroofgenius': 'https://www.myroofgenius.com',
            'system_health': '81.8%',
            'revenue_focus': 'MyRoofGenius only',
            'last_update': datetime.utcnow().isoformat()
        }

# Initialize on import
bridge = ContextBridge()
EOF

# 3. Create initial context file
cat > ~/.ai_context/current.json << 'EOF'
{
  "system_status": {
    "value": {
      "backend": "v4.35",
      "backend_url": "https://brainops-backend-prod.onrender.com",
      "myroofgenius": "https://www.myroofgenius.com",
      "health": "81.8% operational",
      "focus": "Revenue generation via MyRoofGenius"
    },
    "timestamp": "2025-08-17T00:00:00Z"
  },
  "critical_info": {
    "value": {
      "centerpoint_not_revenue": true,
      "only_revenue_source": "MyRoofGenius",
      "pricing_tiers": ["$97", "$297", "$997"],
      "lead_api_workaround": "Use backend API directly"
    },
    "timestamp": "2025-08-17T00:00:00Z"
  },
  "current_goals": {
    "value": {
      "immediate": "Generate traffic to MyRoofGenius",
      "target": "First paying customer",
      "approach": "Reddit, LinkedIn, Google Ads"
    },
    "timestamp": "2025-08-17T00:00:00Z"
  }
}
EOF

# 4. Create context loader script
cat > ~/code/load_context.py << 'EOF'
#!/usr/bin/env python3
from context_bridge import bridge

# Load and display current context
context = bridge.get_context()
status = bridge.get_status()

print("🧠 CURRENT CONTEXT:")
print("-" * 50)
for key, data in context.items():
    print(f"{key}: {data.get('value')}")
print("-" * 50)
print(f"System Status: {status}")
EOF

chmod +x ~/code/load_context.py

# 5. Create Supabase table (if not exists)
cat > ~/code/create_ai_memory_table.sql << 'EOF'
-- Create AI memory table for persistent context
CREATE TABLE IF NOT EXISTS ai_memory (
    id TEXT PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for fast lookups
CREATE INDEX IF NOT EXISTS idx_ai_memory_key ON ai_memory(key);

-- Enable RLS
ALTER TABLE ai_memory ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY "Service role has full access" ON ai_memory
    FOR ALL USING (true);
EOF

# 6. Add to bashrc for automatic loading
echo '
# AI Context Bridge
export AI_CONTEXT_FILE=~/.ai_context/current.json
alias context="python3 ~/code/load_context.py"
alias save-context="python3 -c \"from context_bridge import bridge; bridge.save_context(\$1, \$2)\""
' >> ~/.bashrc

echo "✅ Persistent Memory System Setup Complete!"
echo ""
echo "Usage:"
echo "  context          - View current context"
echo "  save-context     - Save new context"
echo "  python3 -c 'from context_bridge import bridge; print(bridge.get_status())'"
echo ""
echo "The system will now maintain context between sessions!"