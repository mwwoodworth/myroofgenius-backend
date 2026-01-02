"""
SystemArchitectAgent - Maintains complete system awareness
This agent knows everything about our architecture and keeps it updated.
"""

import os
import json
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
import subprocess
import httpx
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core import Agent, MemoryType, MessageType, SystemComponent

logger = logging.getLogger(__name__)

class SystemArchitectAgent(Agent):
    """
    The master architect who knows the entire system architecture.
    Maintains SYSTEM-TRUTH.md and ensures all components are aligned.
    """
    
    def __init__(self):
        super().__init__(
            name="SystemArchitect",
            specialization="system_architecture",
            capabilities=[
                "architecture_mapping",
                "component_tracking",
                "dependency_analysis",
                "documentation_maintenance",
                "system_health_monitoring",
                "deployment_tracking"
            ]
        )
        
        # System knowledge
        self.repositories = {
            'backend': '/home/matt-woodworth/fastapi-operator-env',
            'frontend_mrg': '/home/matt-woodworth/myroofgenius-app',
            'frontend_wc': '/home/matt-woodworth/weathercraft-erp'
        }
        
        self.deployments = {
            'backend': 'https://brainops-backend-prod.onrender.com',
            'frontend_mrg': 'https://myroofgenius.com',
            'frontend_wc': 'https://weathercraft-erp.vercel.app'
        }
        
        self.database = {
            'provider': 'Supabase',
            'host': os.getenv("DB_HOST"),
            'database': os.getenv("DB_NAME", "postgres"),
            'tables_count': 400  # Will update dynamically
        }
    
    async def scan_system(self) -> Dict[str, Any]:
        """
        Perform complete system scan and update knowledge
        """
        scan_result = {
            'timestamp': datetime.utcnow().isoformat(),
            'repositories': {},
            'deployments': {},
            'database': {},
            'issues': [],
            'recommendations': []
        }
        
        # Scan repositories
        for repo_name, repo_path in self.repositories.items():
            if os.path.exists(repo_path):
                repo_info = await self._scan_repository(repo_path)
                scan_result['repositories'][repo_name] = repo_info
                
                # Check for issues
                if repo_info.get('uncommitted_changes'):
                    scan_result['issues'].append({
                        'type': 'uncommitted_changes',
                        'repository': repo_name,
                        'details': f"{repo_info['uncommitted_changes']} uncommitted files"
                    })
            else:
                scan_result['issues'].append({
                    'type': 'missing_repository',
                    'repository': repo_name,
                    'expected_path': repo_path
                })
        
        # Check deployments
        for deploy_name, deploy_url in self.deployments.items():
            deployment_info = await self._check_deployment(deploy_url)
            scan_result['deployments'][deploy_name] = deployment_info
            
            if not deployment_info['healthy']:
                scan_result['issues'].append({
                    'type': 'deployment_unhealthy',
                    'deployment': deploy_name,
                    'url': deploy_url,
                    'status': deployment_info.get('status_code', 'unreachable')
                })
        
        # Check database
        scan_result['database'] = await self._check_database()
        
        # Store scan result in memory
        await self.memory.remember(
            MemoryType.KNOWLEDGE,
            scan_result,
            relevance=1.0
        )
        
        # Update system state
        await self._update_system_state(scan_result)
        
        # Generate recommendations
        scan_result['recommendations'] = await self._generate_recommendations(scan_result)
        
        return scan_result
    
    async def _scan_repository(self, repo_path: str) -> Dict[str, Any]:
        """Scan a git repository"""
        repo_info = {
            'path': repo_path,
            'exists': True,
            'git_initialized': False,
            'current_branch': None,
            'last_commit': None,
            'uncommitted_changes': 0,
            'file_count': 0,
            'primary_language': None
        }
        
        try:
            # Check if git repo
            if os.path.exists(os.path.join(repo_path, '.git')):
                repo_info['git_initialized'] = True
                
                # Get current branch
                result = subprocess.run(
                    ['git', 'branch', '--show-current'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                )
                repo_info['current_branch'] = result.stdout.strip()
                
                # Get last commit
                result = subprocess.run(
                    ['git', 'log', '-1', '--format=%H %s'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                )
                repo_info['last_commit'] = result.stdout.strip()
                
                # Check for uncommitted changes
                result = subprocess.run(
                    ['git', 'status', '--porcelain'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                )
                repo_info['uncommitted_changes'] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            # Count files
            for root, dirs, files in os.walk(repo_path):
                # Skip hidden and node_modules
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
                repo_info['file_count'] += len(files)
            
            # Detect primary language
            extensions = {}
            for root, dirs, files in os.walk(repo_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
                for file in files:
                    ext = Path(file).suffix
                    if ext:
                        extensions[ext] = extensions.get(ext, 0) + 1
            
            if extensions:
                primary_ext = max(extensions.items(), key=lambda x: x[1])[0]
                language_map = {
                    '.py': 'Python',
                    '.js': 'JavaScript',
                    '.ts': 'TypeScript',
                    '.tsx': 'TypeScript React',
                    '.jsx': 'JavaScript React'
                }
                repo_info['primary_language'] = language_map.get(primary_ext, primary_ext)
        
        except Exception as e:
            repo_info['error'] = str(e)
        
        return repo_info
    
    async def _check_deployment(self, url: str) -> Dict[str, Any]:
        """Check deployment health"""
        deployment_info = {
            'url': url,
            'healthy': False,
            'status_code': None,
            'response_time': None,
            'error': None
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                start_time = datetime.utcnow()
                
                # Try health endpoint first
                health_url = f"{url}/health" if not url.endswith('/health') else url
                try:
                    response = await client.get(health_url)
                    deployment_info['status_code'] = response.status_code
                    deployment_info['response_time'] = (datetime.utcnow() - start_time).total_seconds()
                    
                    if response.status_code == 200:
                        deployment_info['healthy'] = True
                        try:
                            data = response.json()
                            if isinstance(data, dict):
                                deployment_info['version'] = data.get('version')
                                deployment_info['status'] = data.get('status')
                        except:
                            pass
                except:
                    # Try base URL
                    response = await client.get(url)
                    deployment_info['status_code'] = response.status_code
                    deployment_info['response_time'] = (datetime.utcnow() - start_time).total_seconds()
                    deployment_info['healthy'] = response.status_code == 200
        
        except Exception as e:
            deployment_info['error'] = str(e)
        
        return deployment_info
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database status"""
        db_info = {
            'connected': False,
            'tables': 0,
            'centerpoint_records': 0,
            'ai_agents': 0,
            'error': None
        }
        
        try:
            async with self.pool.acquire() as conn:
                # Count tables
                result = await conn.fetchval("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                db_info['tables'] = result
                
                # Count CenterPoint records
                result = await conn.fetchval("""
                    SELECT COUNT(*) FROM centerpoint_companies
                """)
                db_info['centerpoint_records'] = result
                
                # Count AI agents
                result = await conn.fetchval("""
                    SELECT COUNT(*) FROM ai_agents
                """)
                db_info['ai_agents'] = result
                
                db_info['connected'] = True
        
        except Exception as e:
            db_info['error'] = str(e)
        
        return db_info
    
    async def _update_system_state(self, scan_result: Dict[str, Any]):
        """Update system state in database"""
        try:
            async with self.pool.acquire() as conn:
                for component_name, component_data in scan_result['repositories'].items():
                    await conn.execute("""
                        INSERT INTO system_state (state_id, component, health_status, last_check, metrics, issues, agent_owner)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (component) DO UPDATE SET
                            health_status = $3,
                            last_check = $4,
                            metrics = $5,
                            issues = $6
                    """, 
                        str(uuid.uuid4()),
                        component_name,
                        'healthy' if not component_data.get('uncommitted_changes') else 'warning',
                        datetime.utcnow(),
                        json.dumps(component_data),
                        json.dumps([]),
                        self.agent_id
                    )
                
                for component_name, component_data in scan_result['deployments'].items():
                    await conn.execute("""
                        INSERT INTO system_state (state_id, component, health_status, last_check, metrics, issues, agent_owner)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (component) DO UPDATE SET
                            health_status = $3,
                            last_check = $4,
                            metrics = $5,
                            issues = $6
                    """,
                        str(uuid.uuid4()),
                        f"deployment_{component_name}",
                        'healthy' if component_data['healthy'] else 'error',
                        datetime.utcnow(),
                        json.dumps(component_data),
                        json.dumps([]),
                        self.agent_id
                    )
        
        except Exception as e:
            logger.error(f"Failed to update system state: {e}")
    
    async def _generate_recommendations(self, scan_result: Dict[str, Any]) -> List[Dict]:
        """Generate recommendations based on scan"""
        recommendations = []
        
        # Check for uncommitted changes
        for issue in scan_result['issues']:
            if issue['type'] == 'uncommitted_changes':
                recommendations.append({
                    'priority': 'medium',
                    'action': 'commit_changes',
                    'repository': issue['repository'],
                    'description': f"Commit {issue['details']} in {issue['repository']}"
                })
            
            elif issue['type'] == 'deployment_unhealthy':
                recommendations.append({
                    'priority': 'high',
                    'action': 'fix_deployment',
                    'deployment': issue['deployment'],
                    'description': f"Fix {issue['deployment']} deployment at {issue['url']}"
                })
            
            elif issue['type'] == 'missing_repository':
                recommendations.append({
                    'priority': 'critical',
                    'action': 'restore_repository',
                    'repository': issue['repository'],
                    'description': f"Repository {issue['repository']} not found at expected location"
                })
        
        # Check database
        if not scan_result['database'].get('connected'):
            recommendations.append({
                'priority': 'critical',
                'action': 'fix_database_connection',
                'description': 'Database connection failed - check credentials and network'
            })
        
        return recommendations
    
    async def update_documentation(self):
        """Update SYSTEM-TRUTH.md with current state"""
        # Get latest scan
        latest_memory = await self.memory.recall(MemoryType.KNOWLEDGE, limit=1)
        
        if not latest_memory:
            await self.scan_system()
            latest_memory = await self.memory.recall(MemoryType.KNOWLEDGE, limit=1)
        
        if latest_memory:
            scan_data = latest_memory[0]['content']
            
            # Generate documentation
            doc_content = self._generate_documentation(scan_data)
            
            # Write to file
            doc_path = '/home/matt-woodworth/SYSTEM-TRUTH.md'
            with open(doc_path, 'w') as f:
                f.write(doc_content)
            
            # Remember we updated it
            await self.memory.remember(
                MemoryType.EXPERIENCE,
                {
                    'action': 'documentation_updated',
                    'path': doc_path,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
    
    def _generate_documentation(self, scan_data: Dict) -> str:
        """Generate SYSTEM-TRUTH.md content"""
        doc = f"""# 🚨 SYSTEM TRUTH - Real-Time Architecture Status

## Generated by SystemArchitectAgent
**Last Updated**: {datetime.utcnow().isoformat()}
**Agent ID**: {self.agent_id}

## 🏗️ CURRENT ARCHITECTURE

### Repositories
"""
        
        for repo_name, repo_data in scan_data.get('repositories', {}).items():
            status = "✅" if not repo_data.get('uncommitted_changes') else "⚠️"
            doc += f"""
#### {repo_name}
- **Status**: {status}
- **Path**: {repo_data.get('path')}
- **Branch**: {repo_data.get('current_branch', 'unknown')}
- **Files**: {repo_data.get('file_count', 0)}
- **Language**: {repo_data.get('primary_language', 'unknown')}
- **Uncommitted Changes**: {repo_data.get('uncommitted_changes', 0)}
"""
        
        doc += "\n### Deployments\n"
        
        for deploy_name, deploy_data in scan_data.get('deployments', {}).items():
            status = "✅" if deploy_data.get('healthy') else "❌"
            doc += f"""
#### {deploy_name}
- **Status**: {status}
- **URL**: {deploy_data.get('url')}
- **Response Time**: {deploy_data.get('response_time', 'N/A')}s
- **Version**: {deploy_data.get('version', 'unknown')}
"""
        
        doc += "\n### Database\n"
        db = scan_data.get('database', {})
        doc += f"""
- **Connected**: {"✅" if db.get('connected') else "❌"}
- **Tables**: {db.get('tables', 0)}
- **CenterPoint Records**: {db.get('centerpoint_records', 0)}
- **AI Agents**: {db.get('ai_agents', 0)}
"""
        
        if scan_data.get('issues'):
            doc += "\n## 🚨 CURRENT ISSUES\n"
            for issue in scan_data['issues']:
                doc += f"- **{issue['type']}**: {issue.get('details', issue)}\n"
        
        if scan_data.get('recommendations'):
            doc += "\n## 📋 RECOMMENDATIONS\n"
            for rec in scan_data['recommendations']:
                priority_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(rec['priority'], "⚪")
                doc += f"- {priority_emoji} **{rec['priority'].upper()}**: {rec['description']}\n"
        
        doc += """
---
*This document is automatically maintained by the SystemArchitectAgent*
"""
        
        return doc
    
    async def handle_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle queries from other agents"""
        query_type = query.get('type')
        
        if query_type == 'system_status':
            return await self.scan_system()
        
        elif query_type == 'component_info':
            component = query.get('component')
            # Retrieve from memory
            memories = await self.memory.search(component, limit=1)
            if memories:
                return memories[0]['content']
            else:
                # Scan and return
                scan = await self.scan_system()
                return scan.get('repositories', {}).get(component, {})
        
        elif query_type == 'deployment_status':
            deployment = query.get('deployment')
            return await self._check_deployment(self.deployments.get(deployment, deployment))
        
        else:
            return {'error': f'Unknown query type: {query_type}'}
    
    async def run(self):
        """Main agent loop"""
        await self.initialize()
        
        while True:
            try:
                # Periodic system scan (every 5 minutes)
                await self.scan_system()
                await self.update_documentation()
                
                # Check for messages from other agents
                messages = await self.communication.receive(limit=10)
                
                for message in messages:
                    if message['message_type'] == MessageType.QUERY.value:
                        # Handle query
                        response = await self.handle_query(message['content'])
                        
                        # Send response
                        await self.communication.send(
                            message['from_agent'],
                            MessageType.RESPONSE,
                            response
                        )
                    
                    elif message['message_type'] == MessageType.ALERT.value:
                        # React to alerts
                        alert = message['content']
                        
                        # Log alert
                        await self.memory.remember(
                            MemoryType.EXPERIENCE,
                            {
                                'alert': alert,
                                'from': message['from_agent'],
                                'timestamp': datetime.utcnow().isoformat()
                            }
                        )
                        
                        # Trigger system scan if critical
                        if alert.get('severity') == 'critical':
                            await self.scan_system()
                            await self.update_documentation()
                
                # Learn from experiences
                if datetime.utcnow().minute % 30 == 0:  # Every 30 minutes
                    await self.learn()
                
                # Sleep before next cycle
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"SystemArchitectAgent error: {e}")
                
                # Remember error
                await self.memory.remember(
                    MemoryType.ERROR,
                    {
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                
                await asyncio.sleep(60)  # Wait 1 minute on error

# Agent instance
system_architect = SystemArchitectAgent()