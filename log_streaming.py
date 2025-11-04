"""
Complete Log Streaming System
Real-time log aggregation and streaming from all services
"""

import asyncio
import json
from datetime import datetime, UTC
from typing import AsyncGenerator, Dict, Any, Optional
import aioredis
import asyncpg
from fastapi import WebSocket
import httpx
from collections import deque
import re

class LogStreamingService:
    def __init__(self, db_pool: asyncpg.Pool, redis: aioredis.Redis):
        self.db_pool = db_pool
        self.redis = redis
        self.streams = {}
        self.subscribers = set()
        self.log_buffer = deque(maxlen=10000)
        self.filters = {}
        
    async def start_streaming(self):
        """Start all log streams"""
        tasks = [
            asyncio.create_task(self.stream_vercel_logs()),
            asyncio.create_task(self.stream_render_logs()),
            asyncio.create_task(self.stream_application_logs()),
            asyncio.create_task(self.process_log_pipeline()),
            asyncio.create_task(self.monitor_log_health())
        ]
        await asyncio.gather(*tasks)
    
    async def stream_vercel_logs(self):
        """Stream logs from Vercel"""
        vercel_token = os.getenv('VERCEL_TOKEN')
        team_id = os.getenv('VERCEL_TEAM_ID')
        
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    async with client.stream(
                        'GET',
                        f'https://api.vercel.com/v1/teams/{team_id}/logs',
                        headers={'Authorization': f'Bearer {vercel_token}'},
                        params={
                            'follow': 'true',
                            'format': 'ndjson',
                            'source': 'all'
                        }
                    ) as response:
                        async for line in response.aiter_lines():
                            if line:
                                log_entry = json.loads(line)
                                await self.process_log('vercel', log_entry)
                                
                except Exception as e:
                    print(f"Vercel stream error: {e}")
                    await asyncio.sleep(5)
    
    async def stream_render_logs(self):
        """Stream logs from Render"""
        render_api_key = os.getenv('RENDER_API_KEY')
        service_id = os.getenv('RENDER_SERVICE_ID')
        
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    async with client.stream(
                        'GET',
                        f'https://api.render.com/v1/services/{service_id}/logs',
                        headers={'Authorization': f'Bearer {render_api_key}'},
                        params={'tail': 'true'}
                    ) as response:
                        async for line in response.aiter_lines():
                            if line:
                                log_entry = self.parse_render_log(line)
                                await self.process_log('render', log_entry)
                                
                except Exception as e:
                    print(f"Render stream error: {e}")
                    await asyncio.sleep(5)
    
    async def stream_application_logs(self):
        """Stream application logs from Redis pub/sub"""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe('logs:application')
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                log_data = json.loads(message['data'])
                await self.process_log('application', log_data)
    
    async def process_log(self, source: str, log_entry: Dict):
        """Process incoming log entry"""
        # Standardize log format
        standardized = self.standardize_log(source, log_entry)
        
        # Add metadata
        standardized['source'] = source
        standardized['received_at'] = datetime.now(UTC).isoformat()
        
        # Apply filters
        if self.should_filter(standardized):
            return
        
        # Store in buffer
        self.log_buffer.append(standardized)
        
        # Store in database for persistence
        await self.store_log(standardized)
        
        # Broadcast to subscribers
        await self.broadcast_log(standardized)
        
        # Check for alerts
        await self.check_log_alerts(standardized)
    
    def standardize_log(self, source: str, log_entry: Dict) -> Dict:
        """Standardize log format across sources"""
        standardized = {
            'timestamp': None,
            'level': 'info',
            'message': '',
            'metadata': {}
        }
        
        if source == 'vercel':
            standardized['timestamp'] = log_entry.get('timestamp')
            standardized['level'] = log_entry.get('level', 'info')
            standardized['message'] = log_entry.get('message', '')
            standardized['metadata'] = {
                'deployment_id': log_entry.get('deploymentId'),
                'request_id': log_entry.get('requestId'),
                'path': log_entry.get('path')
            }
            
        elif source == 'render':
            standardized['timestamp'] = log_entry.get('timestamp')
            standardized['message'] = log_entry.get('text', '')
            standardized['metadata'] = {
                'service': log_entry.get('service'),
                'instance': log_entry.get('instance')
            }
            
        elif source == 'application':
            standardized.update(log_entry)
        
        return standardized
    
    def parse_render_log(self, line: str) -> Dict:
        """Parse Render log line"""
        # Render logs come in various formats
        match = re.match(r'^(\S+)\s+(\S+)\s+(.*)$', line)
        if match:
            return {
                'timestamp': match.group(1),
                'service': match.group(2),
                'text': match.group(3)
            }
        return {'text': line}
    
    async def store_log(self, log_entry: Dict):
        """Store log in database"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO logs (
                    source, timestamp, level, message, metadata
                ) VALUES ($1, $2, $3, $4, $5)
            """, log_entry['source'], 
                log_entry['timestamp'] or datetime.now(UTC),
                log_entry['level'],
                log_entry['message'],
                json.dumps(log_entry['metadata']))
    
    async def broadcast_log(self, log_entry: Dict):
        """Broadcast log to all subscribers"""
        message = json.dumps(log_entry)
        
        # Broadcast to WebSocket subscribers
        dead_subscribers = set()
        for subscriber in self.subscribers:
            try:
                await subscriber.send_text(message)
            except:
                dead_subscribers.add(subscriber)
        
        # Clean up dead connections
        self.subscribers -= dead_subscribers
        
        # Publish to Redis for other services
        await self.redis.publish('logs:stream', message)
    
    async def check_log_alerts(self, log_entry: Dict):
        """Check if log triggers any alerts"""
        # Error detection
        if log_entry['level'] in ['error', 'critical', 'fatal']:
            await self.handle_error_log(log_entry)
        
        # Pattern matching for known issues
        patterns = {
            'out of memory': 'memory_issue',
            'database connection failed': 'database_issue',
            'rate limit exceeded': 'rate_limit_issue',
            'deployment failed': 'deployment_issue'
        }
        
        message_lower = log_entry['message'].lower()
        for pattern, issue_type in patterns.items():
            if pattern in message_lower:
                await self.trigger_alert(issue_type, log_entry)
    
    async def handle_error_log(self, log_entry: Dict):
        """Handle error logs"""
        # Increment error counter
        error_key = f"errors:{log_entry['source']}:{datetime.now(UTC).strftime('%Y%m%d%H')}"
        await self.redis.incr(error_key)
        await self.redis.expire(error_key, 86400)  # Keep for 24 hours
        
        # Check error rate
        count = await self.redis.get(error_key)
        if int(count or 0) > 100:  # More than 100 errors per hour
            await self.trigger_alert('high_error_rate', log_entry)
    
    async def trigger_alert(self, alert_type: str, context: Dict):
        """Trigger alert for log issue"""
        alert = {
            'type': alert_type,
            'timestamp': datetime.now(UTC).isoformat(),
            'context': context,
            'severity': self.get_alert_severity(alert_type)
        }
        
        # Store alert
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO alerts (type, severity, context, created_at)
                VALUES ($1, $2, $3, $4)
            """, alert_type, alert['severity'], 
                json.dumps(context), datetime.now(UTC))
        
        # Send notifications
        if alert['severity'] in ['high', 'critical']:
            await self.send_urgent_notification(alert)
    
    def get_alert_severity(self, alert_type: str) -> str:
        """Get severity level for alert type"""
        severities = {
            'memory_issue': 'high',
            'database_issue': 'critical',
            'rate_limit_issue': 'medium',
            'deployment_issue': 'high',
            'high_error_rate': 'high'
        }
        return severities.get(alert_type, 'low')
    
    async def subscribe_to_logs(self, websocket: WebSocket, filters: Optional[Dict] = None):
        """Subscribe to log stream via WebSocket"""
        self.subscribers.add(websocket)
        
        if filters:
            self.filters[websocket] = filters
        
        try:
            # Send recent logs
            for log in list(self.log_buffer)[-100:]:
                if self.matches_filter(log, filters):
                    await websocket.send_json(log)
            
            # Keep connection alive
            while True:
                await asyncio.sleep(30)
                await websocket.send_json({'type': 'ping'})
                
        except Exception:
            self.subscribers.discard(websocket)
            self.filters.pop(websocket, None)
    
    def matches_filter(self, log: Dict, filters: Optional[Dict]) -> bool:
        """Check if log matches filters"""
        if not filters:
            return True
        
        for key, value in filters.items():
            if key not in log:
                return False
            if isinstance(value, list):
                if log[key] not in value:
                    return False
            elif log[key] != value:
                return False
        
        return True
    
    def should_filter(self, log: Dict) -> bool:
        """Check if log should be filtered out"""
        # Filter out noise
        noise_patterns = [
            'health check',
            'ping',
            'OPTIONS',
            '/favicon.ico'
        ]
        
        message = log.get('message', '').lower()
        return any(pattern in message for pattern in noise_patterns)
    
    async def get_logs(self, 
                      source: Optional[str] = None,
                      level: Optional[str] = None,
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None,
                      limit: int = 1000) -> list:
        """Query logs from database"""
        query = """
            SELECT * FROM logs 
            WHERE 1=1
        """
        params = []
        
        if source:
            params.append(source)
            query += f" AND source = ${len(params)}"
        
        if level:
            params.append(level)
            query += f" AND level = ${len(params)}"
        
        if start_time:
            params.append(start_time)
            query += f" AND timestamp >= ${len(params)}"
        
        if end_time:
            params.append(end_time)
            query += f" AND timestamp <= ${len(params)}"
        
        query += f" ORDER BY timestamp DESC LIMIT {limit}"
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def monitor_log_health(self):
        """Monitor log streaming health"""
        while True:
            try:
                stats = await self.get_log_stats()
                
                # Check log volume
                if stats['total_last_hour'] == 0:
                    await self.trigger_alert('no_logs', stats)
                
                # Check error rate
                error_rate = stats['errors_last_hour'] / max(stats['total_last_hour'], 1)
                if error_rate > 0.05:  # >5% errors
                    await self.trigger_alert('high_error_rate', stats)
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                print(f"Log monitoring error: {e}")
    
    async def get_log_stats(self) -> Dict:
        """Get log statistics"""
        async with self.db_pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_last_hour,
                    COUNT(*) FILTER (WHERE level IN ('error', 'critical')) as errors_last_hour,
                    COUNT(DISTINCT source) as active_sources
                FROM logs
                WHERE timestamp > NOW() - INTERVAL '1 hour'
            """)
            
            return dict(stats)

# API endpoints
async def stream_logs_endpoint(websocket: WebSocket, source: Optional[str] = None):
    """WebSocket endpoint for streaming logs"""
    await websocket.accept()
    
    filters = {}
    if source:
        filters['source'] = source
    
    await log_service.subscribe_to_logs(websocket, filters)

async def get_logs_endpoint(
    source: Optional[str] = None,
    level: Optional[str] = None,
    hours: int = 1
):
    """REST endpoint for querying logs"""
    start_time = datetime.now(UTC) - timedelta(hours=hours)
    
    logs = await log_service.get_logs(
        source=source,
        level=level,
        start_time=start_time
    )
    
    return {'logs': logs, 'count': len(logs)}