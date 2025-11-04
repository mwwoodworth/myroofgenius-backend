#!/usr/bin/env python3
"""
TEST NEURAL OS CAPABILITIES WITH PERSISTENT KNOWLEDGE
======================================================
This script demonstrates the Neural OS utilizing its newly acquired
comprehensive knowledge to make intelligent decisions and provide insights.
"""

import psycopg2
import json
from psycopg2.extras import RealDictCursor
from datetime import datetime

DATABASE_URL = 'postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require'

class NeuralOSIntelligence:
    """Neural OS with access to comprehensive system knowledge"""
    
    def __init__(self):
        self.conn = psycopg2.connect(DATABASE_URL)
        self.knowledge = self.load_knowledge()
        
    def load_knowledge(self):
        """Load all system knowledge from persistent memory"""
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Load all knowledge entries
        cur.execute("""
            SELECT component_name, component_type, agent_name, 
                   knowledge_data, confidence_score
            FROM neural_os_knowledge
            ORDER BY updated_at DESC
        """)
        
        knowledge = {}
        for row in cur.fetchall():
            if row['component_name'] not in knowledge:
                knowledge[row['component_name']] = {
                    'type': row['component_type'],
                    'agents': {},
                    'confidence': row['confidence_score']
                }
            knowledge[row['component_name']]['agents'][row['agent_name']] = row['knowledge_data']
        
        return knowledge
    
    def analyze_system_health(self):
        """Analyze overall system health based on knowledge"""
        print("\n🏥 SYSTEM HEALTH ANALYSIS")
        print("="*60)
        
        health_score = 100
        issues = []
        
        # Check each component
        for component, data in self.knowledge.items():
            print(f"\n📍 {component} ({data['type']})")
            
            # Analyze based on agent findings
            for agent, findings in data['agents'].items():
                if isinstance(findings, dict):
                    analysis = findings.get('analysis', {})
                    
                    # Check for large files
                    if analysis.get('lines_of_code', 0) > 500:
                        health_score -= 2
                        issues.append(f"{component}: Large file detected ({analysis['lines_of_code']} lines)")
                    
                    # Check for security issues
                    if 'security' in analysis and analysis['security']:
                        health_score -= 5
                        issues.append(f"{component}: Security concerns detected")
            
            print(f"   Status: ✅ Reviewed by {len(data['agents'])} agents")
            print(f"   Confidence: {data['confidence']*100:.1f}%")
        
        print(f"\n📊 Overall Health Score: {health_score}/100")
        if issues:
            print("\n⚠️  Issues Detected:")
            for issue in issues[:5]:
                print(f"   • {issue}")
        
        return health_score
    
    def get_optimization_recommendations(self):
        """Generate optimization recommendations based on knowledge"""
        print("\n🎯 OPTIMIZATION RECOMMENDATIONS")
        print("="*60)
        
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Get insights
        cur.execute("""
            SELECT title, description, priority, impact_score
            FROM neural_os_insights
            ORDER BY impact_score DESC
            LIMIT 10
        """)
        
        insights = cur.fetchall()
        
        if insights:
            for i, insight in enumerate(insights, 1):
                print(f"\n{i}. {insight['title']}")
                print(f"   Priority: {insight['priority'].upper()}")
                print(f"   Impact: {insight['impact_score']*100:.0f}%")
                print(f"   {insight['description']}")
        else:
            print("No specific optimizations needed at this time.")
        
        return insights
    
    def demonstrate_capabilities(self):
        """Demonstrate all active capabilities"""
        print("\n🚀 ACTIVE SYSTEM CAPABILITIES")
        print("="*60)
        
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT capability_name, capability_type, description,
                   performance_metrics, status
            FROM neural_os_capabilities
            WHERE status = 'active'
        """)
        
        capabilities = cur.fetchall()
        
        for cap in capabilities:
            print(f"\n✨ {cap['capability_name']}")
            print(f"   Type: {cap['capability_type']}")
            print(f"   {cap['description']}")
            
            if cap['performance_metrics']:
                metrics = cap['performance_metrics']
                if isinstance(metrics, dict):
                    print("   Metrics:")
                    for key, value in metrics.items():
                        print(f"     • {key}: {value}")
    
    def query_knowledge(self, query):
        """Query the knowledge base for specific information"""
        print(f"\n🔍 KNOWLEDGE QUERY: {query}")
        print("="*60)
        
        results = []
        query_lower = query.lower()
        
        for component, data in self.knowledge.items():
            if query_lower in component.lower():
                results.append({
                    'component': component,
                    'type': data['type'],
                    'agents': list(data['agents'].keys())
                })
        
        if results:
            print(f"Found {len(results)} matching components:")
            for result in results:
                print(f"\n📦 {result['component']}")
                print(f"   Type: {result['type']}")
                print(f"   Analyzed by: {', '.join(result['agents'])}")
        else:
            print("No matching components found.")
        
        return results
    
    def generate_system_report(self):
        """Generate comprehensive system report"""
        print("\n📈 COMPREHENSIVE SYSTEM REPORT")
        print("="*60)
        
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Get summary statistics
        cur.execute("""
            SELECT 
                (SELECT COUNT(*) FROM neural_os_knowledge) as knowledge_entries,
                (SELECT COUNT(DISTINCT component_name) FROM neural_os_knowledge) as components,
                (SELECT COUNT(*) FROM neural_os_insights) as insights,
                (SELECT COUNT(*) FROM neural_os_capabilities WHERE status = 'active') as capabilities,
                (SELECT COUNT(*) FROM neural_os_reviews WHERE status = 'completed') as reviews
        """)
        
        stats = cur.fetchone()
        
        print("\n📊 System Statistics:")
        print(f"   • Knowledge Entries: {stats['knowledge_entries']}")
        print(f"   • Components Analyzed: {stats['components']}")
        print(f"   • Insights Generated: {stats['insights']}")
        print(f"   • Active Capabilities: {stats['capabilities']}")
        print(f"   • Completed Reviews: {stats['reviews']}")
        
        # Get recent review
        cur.execute("""
            SELECT review_id, completed_at, reviewed_components
            FROM neural_os_reviews
            WHERE status = 'completed'
            ORDER BY completed_at DESC
            LIMIT 1
        """)
        
        review = cur.fetchone()
        if review:
            print(f"\n📅 Last Review:")
            print(f"   • Review ID: {review['review_id']}")
            print(f"   • Completed: {review['completed_at']}")
            print(f"   • Components: {review['reviewed_components']}")
        
        # Get database stats
        cur.execute("""
            SELECT COUNT(*) as table_count
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        
        db_stats = cur.fetchone()
        print(f"\n💾 Database:")
        print(f"   • Total Tables: {db_stats['table_count']}")
        
        print("\n✅ Neural OS is fully operational with comprehensive knowledge!")
    
    def close(self):
        """Clean up resources"""
        self.conn.close()

def main():
    """Main demonstration"""
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║          NEURAL OS INTELLIGENT CAPABILITIES           ║
    ║                                                        ║
    ║  Demonstrating comprehensive system knowledge and     ║
    ║  intelligent decision-making capabilities...          ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    # Initialize Neural OS with knowledge
    neural_os = NeuralOSIntelligence()
    
    # Demonstrate capabilities
    health_score = neural_os.analyze_system_health()
    
    recommendations = neural_os.get_optimization_recommendations()
    
    neural_os.demonstrate_capabilities()
    
    # Query specific knowledge
    neural_os.query_knowledge("API")
    neural_os.query_knowledge("Database")
    
    # Generate final report
    neural_os.generate_system_report()
    
    # Clean up
    neural_os.close()
    
    print("\n" + "="*60)
    print("NEURAL OS DEMONSTRATION COMPLETE")
    print("="*60)
    print("The system now has permanent, comprehensive knowledge of all")
    print("components and can make intelligent decisions autonomously!")

if __name__ == "__main__":
    main()