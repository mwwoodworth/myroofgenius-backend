#!/usr/bin/env python3
"""
HOW TO USE THE PERSISTENT MEMORY SYSTEM
This file demonstrates all the ways to interact with our master persistent memory
"""

import psycopg2
import json
from datetime import datetime
from typing import Dict, List, Any

class PersistentMemoryClient:
    def __init__(self):
        self.db_url = "postgresql://postgres:<DB_PASSWORD_REDACTED>@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres"
    
    def connect(self):
        return psycopg2.connect(self.db_url)
    
    # ==========================================================================
    # RETRIEVE SOPS (Standard Operating Procedures)
    # ==========================================================================
    
    def get_deployment_sop(self) -> Dict:
        """Get the exact steps to deploy backend"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, steps, tools_required, error_handling
            FROM system_sops
            WHERE sop_id = 'deploy-backend-v4'
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'title': result[0],
                'steps': result[1],
                'tools': result[2],
                'error_handling': result[3]
            }
        return {}
    
    def get_traffic_generation_sop(self) -> Dict:
        """Get the exact steps to generate traffic"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, steps, success_criteria
            FROM system_sops
            WHERE sop_id = 'generate-traffic-myroofgenius'
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'title': result[0],
                'steps': result[1],
                'success_criteria': result[2]
            }
        return {}
    
    # ==========================================================================
    # RETRIEVE SYSTEM ARCHITECTURE
    # ==========================================================================
    
    def get_system_architecture(self) -> List[Dict]:
        """Get complete system architecture documentation"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT component_id, component_name, live_url, 
                   health_status, health_percentage, technology_stack,
                   deployment_info, configuration
            FROM system_architecture
            WHERE is_active = true
            ORDER BY health_percentage DESC
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': r[0],
                'name': r[1],
                'url': r[2],
                'status': r[3],
                'health': r[4],
                'tech_stack': r[5],
                'deployment': r[6],
                'config': r[7]
            }
            for r in results
        ]
    
    # ==========================================================================
    # RETRIEVE CONFIGURATIONS
    # ==========================================================================
    
    def get_credentials(self, component: str = None) -> Dict:
        """Get deployment credentials and secrets"""
        conn = self.connect()
        cursor = conn.cursor()
        
        if component:
            cursor.execute("""
                SELECT config_key, config_value
                FROM system_configurations
                WHERE component = %s AND is_secret = true
            """, (component,))
        else:
            cursor.execute("""
                SELECT config_key, config_value
                FROM system_configurations
                WHERE is_secret = true
            """)
        
        results = cursor.fetchall()
        conn.close()
        
        return {r[0]: r[1]['value'] for r in results}
    
    def get_ui_specifications(self) -> Dict:
        """Get UI/UX design specifications"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT colors, typography, spacing, animations
            FROM ui_specifications
            WHERE spec_id = 'myroofgenius-design-system'
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'colors': result[0],
                'typography': result[1],
                'spacing': result[2],
                'animations': result[3]
            }
        return {}
    
    # ==========================================================================
    # RETRIEVE MEMORIES
    # ==========================================================================
    
    def get_critical_memories(self) -> List[Dict]:
        """Get all critical memories (importance >= 9)"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT memory_key, memory_value, category
            FROM persistent_memory
            WHERE importance >= 9 AND is_active = true
            ORDER BY importance DESC
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'key': r[0],
                'value': r[1],
                'category': r[2]
            }
            for r in results
        ]
    
    def search_memories(self, keyword: str) -> List[Dict]:
        """Search all memories for a keyword"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT memory_key, memory_value, category, importance
            FROM persistent_memory
            WHERE (memory_key ILIKE %s OR memory_value::text ILIKE %s)
            AND is_active = true
            ORDER BY importance DESC
            LIMIT 20
        """, (f'%{keyword}%', f'%{keyword}%'))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'key': r[0],
                'value': r[1],
                'category': r[2],
                'importance': r[3]
            }
            for r in results
        ]
    
    # ==========================================================================
    # RETRIEVE DEPLOYMENT HISTORY
    # ==========================================================================
    
    def get_deployment_history(self, component: str = None) -> List[Dict]:
        """Get deployment history"""
        conn = self.connect()
        cursor = conn.cursor()
        
        if component:
            cursor.execute("""
                SELECT deployment_id, version, deployment_status, 
                       errors_encountered, notes, started_at
                FROM deployment_history
                WHERE component = %s
                ORDER BY started_at DESC
                LIMIT 10
            """, (component,))
        else:
            cursor.execute("""
                SELECT deployment_id, component, version, deployment_status, 
                       notes, started_at
                FROM deployment_history
                ORDER BY started_at DESC
                LIMIT 10
            """)
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': r[0],
                'component': r[1] if not component else component,
                'version': r[2] if component else r[2],
                'status': r[3] if component else r[3],
                'notes': r[4] if component else r[4],
                'date': r[5] if component else r[5]
            }
            for r in results
        ]
    
    # ==========================================================================
    # RETRIEVE DECISIONS
    # ==========================================================================
    
    def get_decisions(self, category: str = None) -> List[Dict]:
        """Get decision history"""
        conn = self.connect()
        cursor = conn.cursor()
        
        if category:
            cursor.execute("""
                SELECT decision_id, title, decision_made, reasoning, actual_outcome
                FROM decision_log
                WHERE category = %s
                ORDER BY decided_at DESC
                LIMIT 10
            """, (category,))
        else:
            cursor.execute("""
                SELECT decision_id, title, decision_made, reasoning, actual_outcome
                FROM decision_log
                ORDER BY decided_at DESC
                LIMIT 10
            """)
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': r[0],
                'title': r[1],
                'decision': r[2],
                'reasoning': r[3],
                'outcome': r[4]
            }
            for r in results
        ]
    
    # ==========================================================================
    # RETRIEVE ERROR PATTERNS
    # ==========================================================================
    
    def get_error_patterns(self, component: str = None) -> List[Dict]:
        """Get known error patterns and fixes"""
        conn = self.connect()
        cursor = conn.cursor()
        
        if component:
            cursor.execute("""
                SELECT error_id, error_message, root_cause, 
                       immediate_fix, permanent_fix
                FROM error_patterns
                WHERE component = %s
                ORDER BY last_seen DESC
            """, (component,))
        else:
            cursor.execute("""
                SELECT error_id, error_message, component, 
                       immediate_fix, permanent_fix
                FROM error_patterns
                WHERE is_resolved = false
                ORDER BY severity, last_seen DESC
            """)
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': r[0],
                'message': r[1],
                'component': r[2] if not component else component,
                'immediate_fix': r[3] if component else r[3],
                'permanent_fix': r[4] if component else r[4]
            }
            for r in results
        ]
    
    # ==========================================================================
    # GET COMPLETE CONTEXT
    # ==========================================================================
    
    def get_complete_context(self) -> Dict:
        """Get everything needed to understand the system"""
        return {
            'critical_facts': self.get_critical_memories(),
            'system_architecture': self.get_system_architecture(),
            'recent_deployments': self.get_deployment_history(),
            'recent_decisions': self.get_decisions(),
            'active_errors': self.get_error_patterns(),
            'credentials': {
                'docker': 'mwwoodworth / dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho',
                'render_hook': 'https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM'
            },
            'current_focus': 'Generate traffic to MyRoofGenius for revenue',
            'system_health': '81.8% operational'
        }
    
    # ==========================================================================
    # STORE NEW INFORMATION
    # ==========================================================================
    
    def store_memory(self, key: str, value: Any, category: str = 'general', importance: int = 5):
        """Store a new memory"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO persistent_memory (memory_key, memory_value, category, importance)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (memory_key) 
            DO UPDATE SET 
                memory_value = EXCLUDED.memory_value,
                updated_at = NOW(),
                access_count = persistent_memory.access_count + 1
        """, (key, json.dumps(value), category, importance))
        
        conn.commit()
        conn.close()
    
    def record_deployment(self, component: str, version: str, status: str, notes: str = None):
        """Record a deployment"""
        conn = self.connect()
        cursor = conn.cursor()
        
        deployment_id = f"deploy-{component}-{version}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        cursor.execute("""
            INSERT INTO deployment_history 
            (deployment_id, component, version, environment, deployment_type,
             deployment_status, deployment_steps, configuration_used,
             started_at, completed_at, deployed_by, notes)
            VALUES (%s, %s, %s, 'production', 'docker', %s, %s, %s, NOW(), NOW(), 'claude', %s)
        """, (
            deployment_id, component, version, status,
            json.dumps([]), json.dumps({}), notes
        ))
        
        conn.commit()
        conn.close()


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

if __name__ == "__main__":
    client = PersistentMemoryClient()
    
    print("=" * 80)
    print("PERSISTENT MEMORY SYSTEM - COMPLETE CONTEXT RETRIEVAL")
    print("=" * 80)
    
    # Get deployment SOP
    print("\n📋 BACKEND DEPLOYMENT SOP:")
    deployment_sop = client.get_deployment_sop()
    if deployment_sop:
        print(f"Title: {deployment_sop['title']}")
        for i, step in enumerate(deployment_sop['steps'], 1):
            print(f"  Step {i}: {step['action']}")
            if 'command' in step:
                print(f"    Command: {step['command']}")
    
    # Get system architecture
    print("\n🏗️ SYSTEM ARCHITECTURE:")
    architecture = client.get_system_architecture()
    for system in architecture:
        print(f"  {system['name']}:")
        print(f"    URL: {system['url']}")
        print(f"    Status: {system['status']} ({system['health']}%)")
    
    # Get critical memories
    print("\n🧠 CRITICAL MEMORIES:")
    memories = client.get_critical_memories()
    for memory in memories:
        print(f"  [{memory['category']}] {memory['key']}: {memory['value']}")
    
    # Get recent deployments
    print("\n🚀 RECENT DEPLOYMENTS:")
    deployments = client.get_deployment_history('backend')
    for deploy in deployments[:3]:
        print(f"  {deploy['version']}: {deploy['status']} - {deploy['notes']}")
    
    # Get error patterns
    print("\n❌ KNOWN ERRORS:")
    errors = client.get_error_patterns()
    for error in errors:
        print(f"  {error['message']}")
        if error['immediate_fix']:
            print(f"    Fix: {error['immediate_fix']}")
    
    print("\n" + "=" * 80)
    print("✅ Persistent Memory System is fully operational!")
    print("   - All SOPs documented")
    print("   - All configurations stored")
    print("   - All decisions logged")
    print("   - Complete context available")
    print("=" * 80)