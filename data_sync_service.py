
#!/usr/bin/env python3
'''
Real-time data synchronization service
Keeps frontends in sync with backend
'''

import asyncio
import aiohttp
import json
from datetime import datetime

class DataSyncService:
    def __init__(self):
        self.backend_url = "https://brainops-backend-prod.onrender.com"
        self.sync_interval = 30  # seconds
        
    async def sync_customers(self):
        '''Sync customer data from backend'''
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.backend_url}/api/v1/crm/customers") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Process and store customer data
                    return data
                return None
    
    async def sync_jobs(self):
        '''Sync job data from backend'''
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.backend_url}/api/v1/erp/jobs") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
                return None
    
    async def sync_estimates(self):
        '''Sync estimate data from backend'''
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.backend_url}/api/v1/erp/estimates") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
                return None
    
    async def run_sync_loop(self):
        '''Main synchronization loop'''
        while True:
            try:
                # Sync all data types
                customers = await self.sync_customers()
                jobs = await self.sync_jobs()
                estimates = await self.sync_estimates()
                
                print(f"[{datetime.now()}] Synced: {len(customers or [])} customers, {len(jobs or [])} jobs, {len(estimates or [])} estimates")
                
                # Wait before next sync
                await asyncio.sleep(self.sync_interval)
                
            except Exception as e:
                print(f"Sync error: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    service = DataSyncService()
    asyncio.run(service.run_sync_loop())
