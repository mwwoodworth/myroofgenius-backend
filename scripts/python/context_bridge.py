import json
import os
from datetime import datetime
from supabase import create_client

class ContextBridge:
    def __init__(self):
        # Use existing Supabase connection
        self.supabase = create_client(
            "https://yomagoqdmxszqtdwuhab.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvbWFnb3FkbXhzenF0ZHd1aGFiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTgzMzI3NiwiZXhwIjoyMDY1NDA5Mjc2fQ.7C3guJ_0moYGkdyeFmJ9cd2BmduB5NnU00erIIxH3gQ"
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
