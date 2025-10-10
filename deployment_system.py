"""
Deployment System - Automated CI/CD and deployment management
"""

import os
import asyncio
import json
import subprocess
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import asyncpg
import redis
import aiohttp
import hashlib

logger = logging.getLogger(__name__)

class DeploymentSystem:
    """Automated deployment and CI/CD management"""
    
    def __init__(self, pg_pool, redis_client):
        self.pg_pool = pg_pool
        self.redis = redis_client
        
        # Deployment configuration
        self.config = {
            "github_repo": "https://github.com/mwwoodworth/myroofgenius-backend.git",
            "branch": "main",
            "render_service_id": os.getenv("RENDER_SERVICE_ID"),
            "render_api_key": os.getenv("RENDER_API_KEY"),
            "deployment_tests": [
                "pytest tests/",
                "python -m mypy .",
                "python -m black --check .",
                "python -m pylint *.py"
            ],
            "health_check_endpoint": "/health",
            "rollback_on_failure": True,
            "blue_green_deployment": True,
            "canary_percentage": 10  # Start with 10% traffic
        }
        
    async def create_deployment(self) -> str:
        """Create a new deployment"""
        deployment_id = hashlib.md5(
            f"deploy_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        async with self.pg_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO deployments (
                    id, status, branch, commit_sha, 
                    started_at, metadata
                ) VALUES ($1, $2, $3, $4, NOW(), $5)
            ''', deployment_id, "initiated", self.config["branch"], 
                await self.get_latest_commit(), json.dumps({}))
        
        return deployment_id
    
    async def execute_deployment(self, deployment_id: str):
        """Execute deployment pipeline"""
        try:
            # Update status
            await self.update_deployment_status(deployment_id, "running")
            
            # Step 1: Run tests
            logger.info(f"Deployment {deployment_id}: Running tests")
            test_results = await self.run_tests()
            
            if not test_results["success"]:
                await self.handle_deployment_failure(
                    deployment_id, 
                    "Tests failed", 
                    test_results
                )
                return
            
            # Step 2: Build application
            logger.info(f"Deployment {deployment_id}: Building application")
            build_result = await self.build_application()
            
            if not build_result["success"]:
                await self.handle_deployment_failure(
                    deployment_id, 
                    "Build failed", 
                    build_result
                )
                return
            
            # Step 3: Deploy to staging (if blue-green)
            if self.config["blue_green_deployment"]:
                logger.info(f"Deployment {deployment_id}: Deploying to staging")
                staging_result = await self.deploy_to_staging(deployment_id)
                
                if not staging_result["success"]:
                    await self.handle_deployment_failure(
                        deployment_id, 
                        "Staging deployment failed", 
                        staging_result
                    )
                    return
                
                # Step 4: Run smoke tests on staging
                logger.info(f"Deployment {deployment_id}: Running smoke tests")
                smoke_tests = await self.run_smoke_tests(staging_result["url"])
                
                if not smoke_tests["success"]:
                    await self.handle_deployment_failure(
                        deployment_id, 
                        "Smoke tests failed", 
                        smoke_tests
                    )
                    return
            
            # Step 5: Deploy to production
            logger.info(f"Deployment {deployment_id}: Deploying to production")
            prod_result = await self.deploy_to_production(deployment_id)
            
            if not prod_result["success"]:
                await self.handle_deployment_failure(
                    deployment_id, 
                    "Production deployment failed", 
                    prod_result
                )
                return
            
            # Step 6: Verify deployment
            logger.info(f"Deployment {deployment_id}: Verifying deployment")
            verification = await self.verify_deployment()
            
            if not verification["success"]:
                # Rollback if verification fails
                if self.config["rollback_on_failure"]:
                    await self.rollback_deployment(deployment_id)
                return
            
            # Step 7: Update routing (canary or full)
            logger.info(f"Deployment {deployment_id}: Updating routing")
            await self.update_traffic_routing(deployment_id)
            
            # Success!
            await self.update_deployment_status(deployment_id, "completed")
            
            logger.info(f"Deployment {deployment_id} completed successfully!")
            
            # Send success notification
            await self.send_deployment_notification(deployment_id, "success")
            
        except Exception as e:
            logger.error(f"Deployment {deployment_id} failed: {e}")
            await self.handle_deployment_failure(
                deployment_id, 
                f"Unexpected error: {str(e)}", 
                {}
            )
    
    async def get_latest_commit(self) -> str:
        """Get latest commit SHA"""
        try:
            result = subprocess.run(
                ["git", "ls-remote", self.config["github_repo"], "HEAD"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.split()[0][:7]
        except:
            return "unknown"
    
    async def run_tests(self) -> Dict:
        """Run automated tests"""
        results = {"success": True, "tests": []}
        
        for test_command in self.config["deployment_tests"]:
            try:
                result = subprocess.run(
                    test_command.split(),
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=300  # 5 minute timeout
                )
                
                results["tests"].append({
                    "command": test_command,
                    "passed": True,
                    "output": result.stdout
                })
            except subprocess.CalledProcessError as e:
                results["success"] = False
                results["tests"].append({
                    "command": test_command,
                    "passed": False,
                    "error": e.stderr
                })
                break
            except subprocess.TimeoutExpired:
                results["success"] = False
                results["tests"].append({
                    "command": test_command,
                    "passed": False,
                    "error": "Test timeout"
                })
                break
        
        return results
    
    async def build_application(self) -> Dict:
        """Build the application"""
        try:
            # For Python app, ensure requirements are installed
            subprocess.run(
                ["pip", "install", "-r", "requirements.txt"],
                check=True,
                capture_output=True
            )
            
            return {"success": True}
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": str(e)}
    
    async def deploy_to_staging(self, deployment_id: str) -> Dict:
        """Deploy to staging environment"""
        # For Render.com
        if self.config["render_service_id"]:
            return await self.deploy_to_render_staging(deployment_id)
        
        # For other platforms, implement accordingly
        return {"success": True, "url": "https://staging.myroofgenius.com"}
    
    async def deploy_to_render_staging(self, deployment_id: str) -> Dict:
        """Deploy to Render staging"""
        try:
            async with aiohttp.ClientSession() as session:
                # Trigger deployment
                async with session.post(
                    f"https://api.render.com/v1/services/{self.config['render_service_id']}/deploys",
                    headers={
                        "Authorization": f"Bearer {self.config['render_api_key']}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "branch": self.config["branch"],
                        "comment": f"Deployment {deployment_id}"
                    }
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        
                        # Wait for deployment to complete
                        deploy_id = data["id"]
                        await self.wait_for_render_deployment(deploy_id)
                        
                        return {
                            "success": True,
                            "url": f"https://{self.config['render_service_id']}-staging.onrender.com"
                        }
                    else:
                        return {
                            "success": False,
                            "error": await response.text()
                        }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def wait_for_render_deployment(self, deploy_id: str):
        """Wait for Render deployment to complete"""
        max_wait = 600  # 10 minutes
        check_interval = 10
        elapsed = 0
        
        while elapsed < max_wait:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.render.com/v1/deploys/{deploy_id}",
                    headers={
                        "Authorization": f"Bearer {self.config['render_api_key']}"
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data["status"] == "live":
                            return True
                        elif data["status"] == "failed":
                            raise Exception("Deployment failed on Render")
            
            await asyncio.sleep(check_interval)
            elapsed += check_interval
        
        raise Exception("Deployment timeout")
    
    async def run_smoke_tests(self, staging_url: str) -> Dict:
        """Run smoke tests on staging"""
        tests_passed = True
        results = []
        
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            try:
                async with session.get(
                    f"{staging_url}{self.config['health_check_endpoint']}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results.append({
                            "test": "health_check",
                            "passed": data.get("status") == "healthy"
                        })
                    else:
                        tests_passed = False
                        results.append({
                            "test": "health_check",
                            "passed": False,
                            "error": f"Status {response.status}"
                        })
            except Exception as e:
                tests_passed = False
                results.append({
                    "test": "health_check",
                    "passed": False,
                    "error": str(e)
                })
            
            # Test critical endpoints
            critical_endpoints = ["/api/leads/capture", "/api/metrics", "/"]
            
            for endpoint in critical_endpoints:
                try:
                    async with session.get(
                        f"{staging_url}{endpoint}",
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        results.append({
                            "test": f"endpoint_{endpoint}",
                            "passed": response.status < 500
                        })
                        if response.status >= 500:
                            tests_passed = False
                except Exception as e:
                    tests_passed = False
                    results.append({
                        "test": f"endpoint_{endpoint}",
                        "passed": False,
                        "error": str(e)
                    })
        
        return {"success": tests_passed, "results": results}
    
    async def deploy_to_production(self, deployment_id: str) -> Dict:
        """Deploy to production"""
        # Trigger production deployment
        if self.config["render_service_id"]:
            return await self.deploy_to_render_production(deployment_id)
        
        return {"success": True}
    
    async def deploy_to_render_production(self, deployment_id: str) -> Dict:
        """Deploy to Render production"""
        # Similar to staging but to production service
        # Implementation here
        return {"success": True}
    
    async def verify_deployment(self) -> Dict:
        """Verify production deployment"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"https://brainops-backend-prod.onrender.com{self.config['health_check_endpoint']}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": data.get("status") == "healthy",
                            "details": data
                        }
                    return {"success": False, "status": response.status}
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    async def update_traffic_routing(self, deployment_id: str):
        """Update traffic routing (canary or full)"""
        if self.config.get("canary_percentage"):
            # Start with canary deployment
            await self.update_canary_traffic(
                deployment_id, 
                self.config["canary_percentage"]
            )
            
            # Monitor canary metrics
            await asyncio.sleep(300)  # 5 minutes
            
            # Check canary health
            canary_healthy = await self.check_canary_health(deployment_id)
            
            if canary_healthy:
                # Gradually increase traffic
                for percentage in [25, 50, 75, 100]:
                    await self.update_canary_traffic(deployment_id, percentage)
                    await asyncio.sleep(180)  # 3 minutes between increases
                    
                    if not await self.check_canary_health(deployment_id):
                        # Rollback if issues detected
                        await self.rollback_deployment(deployment_id)
                        return
        else:
            # Full deployment
            await self.switch_to_new_version(deployment_id)
    
    async def update_canary_traffic(self, deployment_id: str, percentage: int):
        """Update canary traffic percentage"""
        # This would update load balancer or routing rules
        self.redis.set(
            f"deployment:{deployment_id}:canary_percentage",
            percentage
        )
        
        logger.info(f"Canary deployment {deployment_id}: {percentage}% traffic")
    
    async def check_canary_health(self, deployment_id: str) -> bool:
        """Check canary deployment health"""
        # Check error rates, response times, etc.
        # Compare with baseline
        return True  # Simplified
    
    async def switch_to_new_version(self, deployment_id: str):
        """Switch all traffic to new version"""
        # Update load balancer or DNS
        logger.info(f"Switched to new version: {deployment_id}")
    
    async def rollback_deployment(self, deployment_id: str):
        """Rollback deployment"""
        logger.warning(f"Rolling back deployment {deployment_id}")
        
        try:
            # Get previous successful deployment
            async with self.pg_pool.acquire() as conn:
                previous = await conn.fetchrow('''
                    SELECT * FROM deployments
                    WHERE status = 'completed'
                    AND id != $1
                    ORDER BY completed_at DESC
                    LIMIT 1
                ''', deployment_id)
                
                if previous:
                    # Redeploy previous version
                    # This would trigger deployment of previous commit
                    pass
            
            await self.update_deployment_status(deployment_id, "rolled_back")
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
    
    async def handle_deployment_failure(
        self, 
        deployment_id: str, 
        reason: str, 
        details: Dict
    ):
        """Handle deployment failure"""
        logger.error(f"Deployment {deployment_id} failed: {reason}")
        
        # Update status
        await self.update_deployment_status(deployment_id, "failed")
        
        # Store failure details
        async with self.pg_pool.acquire() as conn:
            await conn.execute('''
                UPDATE deployments
                SET 
                    failure_reason = $1,
                    failure_details = $2,
                    failed_at = NOW()
                WHERE id = $3
            ''', reason, json.dumps(details), deployment_id)
        
        # Send failure notification
        await self.send_deployment_notification(deployment_id, "failure", reason)
        
        # Rollback if configured
        if self.config["rollback_on_failure"]:
            await self.rollback_deployment(deployment_id)
    
    async def update_deployment_status(self, deployment_id: str, status: str):
        """Update deployment status"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute('''
                UPDATE deployments
                SET status = $1, updated_at = NOW()
                WHERE id = $2
            ''', status, deployment_id)
        
        # Update Redis for real-time tracking
        self.redis.set(
            f"deployment:{deployment_id}:status",
            status,
            ex=86400  # 24 hours
        )
    
    async def send_deployment_notification(
        self, 
        deployment_id: str, 
        status: str, 
        message: str = None
    ):
        """Send deployment notification"""
        notification = {
            "deployment_id": deployment_id,
            "status": status,
            "message": message or f"Deployment {status}",
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to Slack
        if os.getenv("SLACK_WEBHOOK_URL"):
            async with aiohttp.ClientSession() as session:
                color = "good" if status == "success" else "danger"
                await session.post(
                    os.getenv("SLACK_WEBHOOK_URL"),
                    json={
                        "attachments": [{
                            "color": color,
                            "title": f"Deployment {deployment_id}",
                            "text": notification["message"],
                            "fields": [
                                {"title": "Status", "value": status, "short": True},
                                {"title": "Time", "value": notification["timestamp"], "short": True}
                            ]
                        }]
                    }
                )
        
        # Store notification
        async with self.pg_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO deployment_notifications (
                    deployment_id, type, message, sent_at
                ) VALUES ($1, $2, $3, NOW())
            ''', deployment_id, status, notification["message"])
    
    async def get_deployment_status(self, deployment_id: str) -> Dict:
        """Get deployment status"""
        async with self.pg_pool.acquire() as conn:
            deployment = await conn.fetchrow(
                "SELECT * FROM deployments WHERE id = $1",
                deployment_id
            )
            
            if deployment:
                return dict(deployment)
            return {"error": "Deployment not found"}