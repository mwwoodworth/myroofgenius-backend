"""
Security System - Comprehensive security for the entire platform
"""

import os
import asyncio
import json
import hashlib
import hmac
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import asyncpg
import redis
import logging
from cryptography.fernet import Fernet
import re
import ipaddress

logger = logging.getLogger(__name__)

class SecuritySystem:
    """Complete security management system"""
    
    def __init__(self, pg_pool, redis_client):
        self.pg_pool = pg_pool
        self.redis = redis_client
        
        # Encryption key
        self.encryption_key = os.getenv("ENCRYPTION_KEY") or Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
        # JWT secret
        self.jwt_secret = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
        
        # Security rules
        self.security_rules = {
            "max_login_attempts": 5,
            "lockout_duration": 900,  # 15 minutes
            "password_min_length": 12,
            "password_require_special": True,
            "password_require_numbers": True,
            "password_require_uppercase": True,
            "session_timeout": 3600,  # 1 hour
            "api_rate_limit": 100,  # requests per minute
            "sql_injection_patterns": [
                r"(\bunion\b.*\bselect\b|\bselect\b.*\bunion\b)",
                r"(exec|execute|sp_executesql)",
                r"(drop\s+table|truncate\s+table|alter\s+table)",
                r"(<script|javascript:|onerror=|onload=)",
                r"(--|\||;|\/\*|\*\/)"
            ]
        }
        
        # Threat detection patterns
        self.threat_patterns = {
            "sql_injection": re.compile("|".join(self.security_rules["sql_injection_patterns"]), re.IGNORECASE),
            "xss": re.compile(r"(<script|javascript:|onerror=|onload=|<iframe|<object)", re.IGNORECASE),
            "path_traversal": re.compile(r"(\.\.\/|\.\.\\|%2e%2e%2f|%252e%252e%252f)", re.IGNORECASE),
            "command_injection": re.compile(r"(;|\||&&|`|\$\(|\$\{)", re.IGNORECASE)
        }
    
    async def initialize(self):
        """Initialize security system"""
        try:
            # Initialize security tables
            await self._init_security_tables()
            
            # Start security monitoring
            asyncio.create_task(self.continuous_security_scan())
            asyncio.create_task(self.monitor_authentication())
            asyncio.create_task(self.rotate_secrets())
            
            logger.info("Security system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize security: {e}")
    
    async def _init_security_tables(self):
        """Initialize security tables"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS security_events (
                    id SERIAL PRIMARY KEY,
                    event_type VARCHAR(50),
                    severity VARCHAR(20),
                    source_ip VARCHAR(45),
                    user_id VARCHAR(255),
                    details JSONB,
                    threat_score INT,
                    blocked BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS authentication_logs (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255),
                    action VARCHAR(50),
                    success BOOLEAN,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    id SERIAL PRIMARY KEY,
                    key_hash VARCHAR(255) UNIQUE,
                    user_id VARCHAR(255),
                    name VARCHAR(255),
                    permissions JSONB,
                    last_used TIMESTAMP,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW(),
                    active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS blocked_ips (
                    id SERIAL PRIMARY KEY,
                    ip_address VARCHAR(45) UNIQUE,
                    reason TEXT,
                    threat_score INT,
                    blocked_until TIMESTAMP,
                    permanent BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS security_policies (
                    id SERIAL PRIMARY KEY,
                    policy_name VARCHAR(100) UNIQUE,
                    policy_data JSONB,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_security_events_ip ON security_events(source_ip)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_logs_user ON authentication_logs(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_blocked_ips ON blocked_ips(ip_address)")
    
    async def continuous_security_scan(self):
        """Continuously scan for security threats"""
        while True:
            try:
                # Check for suspicious activities
                threats = await self.detect_threats()
                
                if threats:
                    await self.handle_threats(threats)
                
                # Check for vulnerabilities
                await self.scan_vulnerabilities()
                
                # Update threat intelligence
                await self.update_threat_intelligence()
                
                await asyncio.sleep(60)  # Scan every minute
            except Exception as e:
                logger.error(f"Security scan error: {e}")
                await asyncio.sleep(120)
    
    async def detect_threats(self) -> List[Dict]:
        """Detect security threats"""
        threats = []
        
        async with self.pg_pool.acquire() as conn:
            # Check for brute force attempts
            brute_force = await conn.fetch('''
                SELECT user_id, ip_address, COUNT(*) as attempts
                FROM authentication_logs
                WHERE success = FALSE
                AND created_at > NOW() - INTERVAL '15 minutes'
                GROUP BY user_id, ip_address
                HAVING COUNT(*) >= $1
            ''', self.security_rules["max_login_attempts"])
            
            for attempt in brute_force:
                threats.append({
                    "type": "brute_force",
                    "severity": "high",
                    "user_id": attempt["user_id"],
                    "ip_address": attempt["ip_address"],
                    "attempts": attempt["attempts"]
                })
            
            # Check for suspicious API usage
            api_abuse = await conn.fetch('''
                SELECT source_ip, COUNT(*) as requests
                FROM api_metrics
                WHERE recorded_at > NOW() - INTERVAL '1 minute'
                GROUP BY source_ip
                HAVING COUNT(*) > $1
            ''', self.security_rules["api_rate_limit"])
            
            for abuse in api_abuse:
                threats.append({
                    "type": "api_abuse",
                    "severity": "medium",
                    "ip_address": abuse["source_ip"],
                    "requests": abuse["requests"]
                })
            
            # Check for SQL injection attempts
            sql_injection = await conn.fetch('''
                SELECT * FROM security_events
                WHERE event_type = 'sql_injection_attempt'
                AND created_at > NOW() - INTERVAL '5 minutes'
                AND blocked = FALSE
            ''')
            
            for injection in sql_injection:
                threats.append({
                    "type": "sql_injection",
                    "severity": "critical",
                    "details": injection["details"]
                })
        
        return threats
    
    async def handle_threats(self, threats: List[Dict]):
        """Handle detected threats"""
        for threat in threats:
            threat_score = self.calculate_threat_score(threat)
            
            # Log security event
            async with self.pg_pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO security_events (
                        event_type, severity, source_ip, user_id, 
                        details, threat_score, blocked
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ''', threat["type"], threat["severity"], 
                    threat.get("ip_address"), threat.get("user_id"),
                    json.dumps(threat), threat_score, threat_score > 70)
            
            # Take action based on threat score
            if threat_score > 70:
                await self.block_threat(threat)
            elif threat_score > 50:
                await self.throttle_threat(threat)
            
            # Alert if critical
            if threat["severity"] == "critical":
                await self.send_security_alert(threat)
    
    def calculate_threat_score(self, threat: Dict) -> int:
        """Calculate threat score (0-100)"""
        base_scores = {
            "brute_force": 60,
            "api_abuse": 40,
            "sql_injection": 90,
            "xss": 80,
            "path_traversal": 70,
            "command_injection": 85
        }
        
        score = base_scores.get(threat["type"], 50)
        
        # Adjust based on severity
        severity_multipliers = {
            "critical": 1.5,
            "high": 1.2,
            "medium": 1.0,
            "low": 0.8
        }
        
        score *= severity_multipliers.get(threat["severity"], 1.0)
        
        return min(int(score), 100)
    
    async def block_threat(self, threat: Dict):
        """Block a threat"""
        ip_address = threat.get("ip_address")
        
        if ip_address:
            # Add to blocked IPs
            async with self.pg_pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO blocked_ips (
                        ip_address, reason, threat_score, blocked_until
                    ) VALUES ($1, $2, $3, $4)
                    ON CONFLICT (ip_address) 
                    DO UPDATE SET 
                        blocked_until = EXCLUDED.blocked_until,
                        threat_score = EXCLUDED.threat_score
                ''', ip_address, json.dumps(threat), 
                    self.calculate_threat_score(threat),
                    datetime.now() + timedelta(hours=24))
            
            # Update Redis for quick lookup
            self.redis.setex(
                f"blocked_ip:{ip_address}",
                86400,  # 24 hours
                json.dumps(threat)
            )
            
            logger.warning(f"Blocked IP {ip_address} due to {threat['type']}")
    
    async def throttle_threat(self, threat: Dict):
        """Throttle a threat (rate limiting)"""
        ip_address = threat.get("ip_address")
        
        if ip_address:
            # Add rate limiting
            self.redis.setex(
                f"throttled:{ip_address}",
                300,  # 5 minutes
                json.dumps({"limit": 10, "window": 60})
            )
    
    async def send_security_alert(self, threat: Dict):
        """Send security alert"""
        logger.critical(f"SECURITY THREAT: {threat}")
        
        # Store critical alert
        async with self.pg_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO system_alerts (
                    alert_type, severity, message, metadata
                ) VALUES ('security_threat', 'critical', $1, $2)
            ''', f"Security threat detected: {threat['type']}", json.dumps(threat))
    
    async def scan_vulnerabilities(self):
        """Scan for system vulnerabilities"""
        vulnerabilities = []
        
        # Check for outdated dependencies
        # Check for exposed sensitive data
        # Check for misconfigurations
        
        if vulnerabilities:
            await self.report_vulnerabilities(vulnerabilities)
    
    async def report_vulnerabilities(self, vulnerabilities: List[Dict]):
        """Report discovered vulnerabilities"""
        for vuln in vulnerabilities:
            async with self.pg_pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO security_events (
                        event_type, severity, details
                    ) VALUES ('vulnerability_found', $1, $2)
                ''', vuln.get("severity", "medium"), json.dumps(vuln))
    
    async def update_threat_intelligence(self):
        """Update threat intelligence data"""
        # This would connect to threat intelligence feeds
        # For now, we'll maintain internal patterns
        pass
    
    async def monitor_authentication(self):
        """Monitor authentication attempts"""
        while True:
            try:
                await self.check_suspicious_logins()
                await self.enforce_password_policies()
                await self.cleanup_expired_sessions()
                
                await asyncio.sleep(300)  # Every 5 minutes
            except Exception as e:
                logger.error(f"Auth monitoring error: {e}")
                await asyncio.sleep(600)
    
    async def check_suspicious_logins(self):
        """Check for suspicious login patterns"""
        async with self.pg_pool.acquire() as conn:
            # Check for login from new locations
            suspicious = await conn.fetch('''
                SELECT DISTINCT user_id, ip_address
                FROM authentication_logs a1
                WHERE success = TRUE
                AND created_at > NOW() - INTERVAL '1 hour'
                AND NOT EXISTS (
                    SELECT 1 FROM authentication_logs a2
                    WHERE a2.user_id = a1.user_id
                    AND a2.ip_address = a1.ip_address
                    AND a2.created_at < a1.created_at - INTERVAL '1 day'
                )
            ''')
            
            for login in suspicious:
                # Check if IP is from different country/region
                # Send notification to user about new login
                pass
    
    async def enforce_password_policies(self):
        """Enforce password policies"""
        # Check for weak passwords
        # Force password changes for old passwords
        pass
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        # Remove expired JWT tokens from Redis
        for key in self.redis.scan_iter("session:*"):
            session = json.loads(self.redis.get(key))
            if datetime.fromisoformat(session["expires"]) < datetime.now():
                self.redis.delete(key)
    
    async def rotate_secrets(self):
        """Rotate secrets periodically"""
        while True:
            try:
                await asyncio.sleep(86400 * 30)  # Every 30 days
                
                # Rotate API keys
                await self.rotate_api_keys()
                
                # Rotate encryption keys (with migration)
                # This is complex and requires careful data migration
                
            except Exception as e:
                logger.error(f"Secret rotation error: {e}")
    
    async def rotate_api_keys(self):
        """Rotate API keys"""
        async with self.pg_pool.acquire() as conn:
            # Get keys older than 90 days
            old_keys = await conn.fetch('''
                SELECT * FROM api_keys
                WHERE created_at < NOW() - INTERVAL '90 days'
                AND active = TRUE
            ''')
            
            for key in old_keys:
                # Generate new key
                new_key = self.generate_api_key()
                
                # Store new key
                await conn.execute('''
                    INSERT INTO api_keys (
                        key_hash, user_id, name, permissions
                    ) VALUES ($1, $2, $3, $4)
                ''', self.hash_api_key(new_key), key["user_id"],
                    f"{key['name']}_rotated", key["permissions"])
                
                # Mark old key for deprecation
                await conn.execute('''
                    UPDATE api_keys 
                    SET expires_at = NOW() + INTERVAL '7 days'
                    WHERE id = $1
                ''', key["id"])
    
    def generate_api_key(self) -> str:
        """Generate secure API key"""
        return f"sk_{secrets.token_urlsafe(32)}"
    
    def hash_api_key(self, key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    async def validate_request(self, request_data: Dict) -> Tuple[bool, Optional[str]]:
        """Validate incoming request for security threats"""
        # Check IP blacklist
        ip = request_data.get("ip_address")
        if ip and self.redis.exists(f"blocked_ip:{ip}"):
            return False, "IP blocked"
        
        # Check for SQL injection
        for value in request_data.values():
            if isinstance(value, str) and self.threat_patterns["sql_injection"].search(value):
                await self.log_security_event("sql_injection_attempt", ip, request_data)
                return False, "Invalid input detected"
        
        # Check for XSS
        for value in request_data.values():
            if isinstance(value, str) and self.threat_patterns["xss"].search(value):
                await self.log_security_event("xss_attempt", ip, request_data)
                return False, "Invalid input detected"
        
        # Check rate limiting
        if ip and self.redis.exists(f"throttled:{ip}"):
            throttle_data = json.loads(self.redis.get(f"throttled:{ip}"))
            return False, "Rate limit exceeded"
        
        return True, None
    
    async def log_security_event(self, event_type: str, ip: str, details: Dict):
        """Log security event"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO security_events (
                    event_type, source_ip, details, threat_score
                ) VALUES ($1, $2, $3, $4)
            ''', event_type, ip, json.dumps(details), 50)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def generate_jwt(self, user_id: str, expires_in: int = 3600) -> str:
        """Generate JWT token"""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(seconds=expires_in),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def verify_jwt(self, token: str) -> Optional[Dict]:
        """Verify JWT token"""
        try:
            return jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    async def authenticate_user(self, email: str, password: str, ip: str) -> Tuple[bool, Optional[str]]:
        """Authenticate user"""
        async with self.pg_pool.acquire() as conn:
            # Check if IP is blocked
            if self.redis.exists(f"blocked_ip:{ip}"):
                return False, None
            
            # Get user
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1",
                email
            )
            
            if not user:
                # Log failed attempt
                await conn.execute('''
                    INSERT INTO authentication_logs (
                        user_id, action, success, ip_address
                    ) VALUES ($1, 'login', FALSE, $2)
                ''', email, ip)
                return False, None
            
            # Verify password (assuming bcrypt)
            # In production, use proper password hashing
            if not self.verify_password(password, user["password_hash"]):
                # Log failed attempt
                await conn.execute('''
                    INSERT INTO authentication_logs (
                        user_id, action, success, ip_address
                    ) VALUES ($1, 'login', FALSE, $2)
                ''', user["id"], ip)
                return False, None
            
            # Generate token
            token = self.generate_jwt(user["id"])
            
            # Log successful login
            await conn.execute('''
                INSERT INTO authentication_logs (
                    user_id, action, success, ip_address
                ) VALUES ($1, 'login', TRUE, $2)
            ''', user["id"], ip)
            
            # Store session
            self.redis.setex(
                f"session:{token}",
                3600,
                json.dumps({
                    "user_id": user["id"],
                    "ip": ip,
                    "expires": (datetime.now() + timedelta(hours=1)).isoformat()
                })
            )
            
            return True, token
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        # In production, use bcrypt or argon2
        return hashlib.sha256(password.encode()).hexdigest() == password_hash