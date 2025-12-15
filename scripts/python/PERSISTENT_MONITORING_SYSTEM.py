#!/usr/bin/env python3
"""
PERSISTENT MONITORING SYSTEM
24/7 health monitoring with auto-recovery
"""

import os
import time
import json
import requests
import psycopg2
from datetime import datetime, timedelta
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/persistent_monitor.log'),
        logging.StreamHandler()
    ]
)

class PersistentMonitor:
    def __init__(self):
        self.db_url = "postgresql://postgres:<DB_PASSWORD_REDACTED>@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres"
        self.systems = {
            'backend_api': {
                'url': 'https://brainops-backend-prod.onrender.com/api/v1/health',
                'expected_status': 200,
                'critical': True,
                'last_check': None,
                'status': 'unknown',
                'failures': 0
            },
            'myroofgenius': {
                'url': 'https://myroofgenius.com',
                'expected_status': 200,
                'critical': True,
                'last_check': None,
                'status': 'unknown',
                'failures': 0
            },
            'weathercraft_erp': {
                'url': 'https://weathercraft-erp.vercel.app',
                'expected_status': 200,
                'critical': False,
                'last_check': None,
                'status': 'unknown',
                'failures': 0
            },
            'task_os': {
                'url': 'https://brainops-task-os.vercel.app',
                'expected_status': 200,
                'critical': False,
                'last_check': None,
                'status': 'unknown',
                'failures': 0
            },
            'database': {
                'type': 'database',
                'critical': True,
                'last_check': None,
                'status': 'unknown',
                'failures': 0
            },
            'centerpoint_sync': {
                'type': 'process',
                'process_name': 'centerpoint-sync-service.sh',
                'critical': False,
                'last_check': None,
                'status': 'unknown',
                'failures': 0
            }
        }
        
        self.recovery_actions = {
            'backend_api': self.recover_backend,
            'database': self.recover_database,
            'centerpoint_sync': self.recover_sync,
            'myroofgenius': self.recover_frontend,
            'weathercraft_erp': self.recover_frontend,
            'task_os': self.recover_frontend
        }
        
    def check_http_endpoint(self, url, expected_status):
        """Check HTTP endpoint health"""
        try:
            response = requests.get(url, timeout=10, allow_redirects=True)
            return response.status_code == expected_status
        except Exception as e:
            logging.error(f"HTTP check failed for {url}: {e}")
            return False
    
    def check_database(self):
        """Check database connectivity"""
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logging.error(f"Database check failed: {e}")
            return False
    
    def check_process(self, process_name):
        """Check if process is running"""
        try:
            result = subprocess.run(
                f"pgrep -f '{process_name}'",
                shell=True,
                capture_output=True
            )
            return result.returncode == 0
        except Exception as e:
            logging.error(f"Process check failed for {process_name}: {e}")
            return False
    
    def check_system(self, name, config):
        """Check individual system health"""
        healthy = False
        
        if config.get('type') == 'database':
            healthy = self.check_database()
        elif config.get('type') == 'process':
            healthy = self.check_process(config['process_name'])
        else:
            healthy = self.check_http_endpoint(config['url'], config['expected_status'])
        
        # Update status
        old_status = config['status']
        config['status'] = 'healthy' if healthy else 'unhealthy'
        config['last_check'] = datetime.now().isoformat()
        
        # Track failures
        if not healthy:
            config['failures'] += 1
            logging.warning(f"❌ {name}: UNHEALTHY (failures: {config['failures']})")
            
            # Attempt recovery after 3 failures
            if config['failures'] >= 3 and config['critical']:
                logging.info(f"🔧 Attempting recovery for {name}...")
                if name in self.recovery_actions:
                    self.recovery_actions[name](name, config)
        else:
            if old_status == 'unhealthy':
                logging.info(f"✅ {name}: RECOVERED")
            config['failures'] = 0
        
        return healthy
    
    def recover_backend(self, name, config):
        """Attempt to recover backend API"""
        logging.info("Attempting backend recovery...")
        try:
            # Trigger Docker rebuild and deployment
            subprocess.run([
                "/home/mwwoodworth/code/EMERGENCY_BACKEND_RECOVERY.sh"
            ], check=False)
        except Exception as e:
            logging.error(f"Backend recovery failed: {e}")
    
    def recover_database(self, name, config):
        """Attempt to recover database connection"""
        logging.info("Attempting database recovery...")
        try:
            # Run database repair script
            subprocess.run([
                "psql", self.db_url, "-c", "SELECT pg_reload_conf();"
            ], check=False)
        except Exception as e:
            logging.error(f"Database recovery failed: {e}")
    
    def recover_sync(self, name, config):
        """Attempt to recover CenterPoint sync"""
        logging.info("Attempting sync recovery...")
        try:
            subprocess.run([
                "/home/mwwoodworth/code/weathercraft-erp/scripts/start-sync.sh"
            ], check=False)
        except Exception as e:
            logging.error(f"Sync recovery failed: {e}")
    
    def recover_frontend(self, name, config):
        """Attempt to recover frontend application"""
        logging.info(f"Frontend {name} needs redeployment on Vercel")
        # Frontend recovery requires manual Vercel deployment
    
    def store_metrics(self):
        """Store monitoring metrics in database"""
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            
            # Create monitoring table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS system_monitoring (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    system_name VARCHAR(255),
                    status VARCHAR(50),
                    failures INT,
                    metadata JSONB
                )
            """)
            
            # Store current metrics
            for name, config in self.systems.items():
                cur.execute("""
                    INSERT INTO system_monitoring (system_name, status, failures, metadata)
                    VALUES (%s, %s, %s, %s)
                """, (name, config['status'], config['failures'], json.dumps(config)))
            
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logging.error(f"Failed to store metrics: {e}")
    
    def generate_report(self):
        """Generate system health report"""
        total = len(self.systems)
        healthy = sum(1 for s in self.systems.values() if s['status'] == 'healthy')
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_systems': total,
            'healthy_systems': healthy,
            'unhealthy_systems': total - healthy,
            'health_percentage': (healthy / total) * 100 if total > 0 else 0,
            'systems': {}
        }
        
        for name, config in self.systems.items():
            report['systems'][name] = {
                'status': config['status'],
                'failures': config['failures'],
                'last_check': config['last_check'],
                'critical': config.get('critical', False)
            }
        
        # Save report
        with open('/home/mwwoodworth/code/SYSTEM_HEALTH_REPORT.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        logging.info("🔍 Starting monitoring cycle...")
        
        for name, config in self.systems.items():
            self.check_system(name, config)
        
        # Store metrics
        self.store_metrics()
        
        # Generate report
        report = self.generate_report()
        
        # Log summary
        health_pct = report['health_percentage']
        if health_pct >= 90:
            logging.info(f"✅ System Health: {health_pct:.1f}% - OPERATIONAL")
        elif health_pct >= 70:
            logging.warning(f"⚠️ System Health: {health_pct:.1f}% - DEGRADED")
        else:
            logging.error(f"❌ System Health: {health_pct:.1f}% - CRITICAL")
        
        return report
    
    def run_forever(self):
        """Run monitoring continuously"""
        logging.info("🚀 Starting Persistent Monitoring System")
        logging.info("=" * 50)
        
        while True:
            try:
                report = self.run_monitoring_cycle()
                
                # Check if critical systems are down
                critical_down = [
                    name for name, config in self.systems.items()
                    if config['critical'] and config['status'] == 'unhealthy'
                ]
                
                if critical_down:
                    logging.error(f"🚨 CRITICAL SYSTEMS DOWN: {', '.join(critical_down)}")
                
                # Wait before next cycle
                time.sleep(300)  # 5 minutes
                
            except KeyboardInterrupt:
                logging.info("Monitoring stopped by user")
                break
            except Exception as e:
                logging.error(f"Monitoring cycle failed: {e}")
                time.sleep(60)  # Wait 1 minute on error

def main():
    # Create emergency recovery script
    recovery_script = """#!/bin/bash
echo "🚨 EMERGENCY BACKEND RECOVERY"
echo "============================"

# Get latest version
cd /home/mwwoodworth/code/fastapi-operator-env
VERSION=$(grep 'version = ' main.py | cut -d'"' -f2)
echo "Current version: $VERSION"

# Increment patch version
NEW_VERSION="${VERSION%.*}.$((${VERSION##*.} + 1))"
echo "New version: $NEW_VERSION"

# Update version in files
sed -i "s/version = \\"$VERSION\\"/version = \\"$NEW_VERSION\\"/" main.py
sed -i "s/\\"version\\": \\"$VERSION\\"/\\"version\\": \\"$NEW_VERSION\\"/" routes/api_health.py

# Build and push Docker
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'
docker build -t mwwoodworth/brainops-backend:v$NEW_VERSION -f Dockerfile .
docker tag mwwoodworth/brainops-backend:v$NEW_VERSION mwwoodworth/brainops-backend:latest
docker push mwwoodworth/brainops-backend:v$NEW_VERSION
docker push mwwoodworth/brainops-backend:latest

echo "✅ Recovery deployment v$NEW_VERSION pushed"
echo "📌 Manual deployment required on Render"
"""
    
    with open('/home/mwwoodworth/code/EMERGENCY_BACKEND_RECOVERY.sh', 'w') as f:
        f.write(recovery_script)
    os.chmod('/home/mwwoodworth/code/EMERGENCY_BACKEND_RECOVERY.sh', 0o755)
    
    # Start monitoring
    monitor = PersistentMonitor()
    monitor.run_forever()

if __name__ == "__main__":
    main()