#!/usr/bin/env python3
"""Test LangGraph Customer Journey Workflow"""

import asyncio
import uuid
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from ai_orchestration.workflows.customer_journey import customer_journey_workflow

async def test_workflow():
    print('🚀 Testing Customer Journey Workflow...')
    
    # Create a test customer
    test_customer_id = str(uuid.uuid4())
    
    # Run the workflow
    try:
        result = await customer_journey_workflow.run(
            customer_id=test_customer_id,
            initial_metadata={
                'source': 'google_ads',
                'budget': 15000,
                'company': 'Test Corp',
                'phone': '555-1234'
            }
        )
        
        print(f'✅ Workflow completed successfully!')
        print(f'   Customer ID: {test_customer_id}')
        print(f'   Final Stage: {result.get("stage")}')
        print(f'   Score: {result.get("score")}')
        print(f'   Revenue: ${result.get("revenue", 0):.2f}')
        print(f'   Interactions: {len(result.get("interactions", []))}')
        
    except Exception as e:
        print(f'❌ Workflow error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow())