#!/usr/bin/env python3
"""
Admin Review Workflow System
Ensures all products are reviewed and approved before going live
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiohttp
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/admin_review_workflow.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ReviewStatus(Enum):
    """Product review status"""
    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"
    AUTO_APPROVED = "auto_approved"

class ReviewPriority(Enum):
    """Review priority levels"""
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class ReviewRequest:
    """Request for admin review"""
    product_id: str
    product_name: str
    product_type: str
    qa_score: float
    submitted_at: datetime
    priority: ReviewPriority
    review_notes: Optional[str] = None
    reviewer: Optional[str] = None
    review_deadline: Optional[datetime] = None

@dataclass
class ReviewDecision:
    """Admin review decision"""
    review_id: str
    product_id: str
    status: ReviewStatus
    reviewer: str
    reviewed_at: datetime
    comments: str
    required_changes: List[str]
    approval_conditions: List[str]

class AdminReviewWorkflow:
    """Manages the admin review workflow for products"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "https://yomagoqdmxszqtdwuhab.supabase.co")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        self.session = None
        self.auto_approval_threshold = 97.0  # Products with QA score >= 97 can be auto-approved
        self.review_sla_hours = {
            ReviewPriority.URGENT: 2,
            ReviewPriority.HIGH: 8,
            ReviewPriority.MEDIUM: 24,
            ReviewPriority.LOW: 48
        }
        
    async def initialize(self):
        """Initialize the workflow system"""
        self.session = aiohttp.ClientSession()
        logger.info("Admin Review Workflow initialized")
        
    async def submit_for_review(self, product_data: Dict[str, Any], 
                               qa_report: Dict[str, Any]) -> ReviewRequest:
        """Submit a product for admin review"""
        qa_score = qa_report.get('metrics', {}).get('overall_score', 0)
        
        # Determine priority based on score and product type
        if qa_score < 70:
            priority = ReviewPriority.URGENT
        elif qa_score < 85:
            priority = ReviewPriority.HIGH
        elif product_data.get('type') in ['calculator', 'digital_tool']:
            priority = ReviewPriority.HIGH
        else:
            priority = ReviewPriority.MEDIUM
        
        # Calculate review deadline
        review_deadline = datetime.utcnow() + timedelta(
            hours=self.review_sla_hours[priority]
        )
        
        review_request = ReviewRequest(
            product_id=product_data.get('id'),
            product_name=product_data.get('name'),
            product_type=product_data.get('type'),
            qa_score=qa_score,
            submitted_at=datetime.utcnow(),
            priority=priority,
            review_deadline=review_deadline,
            review_notes=self._generate_review_notes(qa_report)
        )
        
        # Check if eligible for auto-approval
        if qa_score >= self.auto_approval_threshold and not self._requires_manual_review(product_data):
            return await self._auto_approve_product(review_request)
        
        # Store review request
        await self._store_review_request(review_request)
        
        # Notify admins
        await self._notify_admins_new_review(review_request)
        
        return review_request
    
    def _generate_review_notes(self, qa_report: Dict[str, Any]) -> str:
        """Generate review notes from QA report"""
        metrics = qa_report.get('metrics', {})
        issues = qa_report.get('issues_found', [])
        
        notes = f"QA Score: {metrics.get('overall_score', 0):.1f}/100\n\n"
        notes += "Score Breakdown:\n"
        notes += f"- Completeness: {metrics.get('completeness_score', 0):.1f}\n"
        notes += f"- Functionality: {metrics.get('functionality_score', 0):.1f}\n"
        notes += f"- Visual Polish: {metrics.get('visual_polish_score', 0):.1f}\n"
        notes += f"- Content Quality: {metrics.get('content_quality_score', 0):.1f}\n"
        notes += f"- Usability: {metrics.get('usability_score', 0):.1f}\n"
        notes += f"- Brand Compliance: {metrics.get('brand_compliance_score', 0):.1f}\n"
        
        if issues:
            notes += "\nIssues Found:\n"
            for issue in issues[:5]:  # Top 5 issues
                notes += f"- [{issue['severity']}] {issue['description']}\n"
        
        return notes
    
    def _requires_manual_review(self, product_data: Dict[str, Any]) -> bool:
        """Check if product requires manual review regardless of score"""
        # Certain product types always require manual review
        manual_review_types = ['contract_template', 'legal_document', 'financial_calculator']
        
        if product_data.get('type') in manual_review_types:
            return True
        
        # New products from new creators require review
        if product_data.get('is_first_product', False):
            return True
        
        # Products with pricing > $100 require review
        if float(product_data.get('price', 0)) > 100:
            return True
        
        return False
    
    async def _auto_approve_product(self, review_request: ReviewRequest) -> ReviewRequest:
        """Auto-approve high-quality products"""
        logger.info(f"Auto-approving product: {review_request.product_name}")
        
        decision = ReviewDecision(
            review_id=f"auto_{review_request.product_id}_{datetime.utcnow().timestamp()}",
            product_id=review_request.product_id,
            status=ReviewStatus.AUTO_APPROVED,
            reviewer="QA_SYSTEM",
            reviewed_at=datetime.utcnow(),
            comments=f"Auto-approved due to high QA score ({review_request.qa_score:.1f})",
            required_changes=[],
            approval_conditions=["Maintain quality standards", "Monitor customer feedback"]
        )
        
        await self._store_review_decision(decision)
        await self._update_product_status(review_request.product_id, 'active')
        
        review_request.reviewer = "QA_SYSTEM"
        return review_request
    
    async def _store_review_request(self, request: ReviewRequest):
        """Store review request in database"""
        try:
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "product_id": request.product_id,
                "product_name": request.product_name,
                "product_type": request.product_type,
                "qa_score": request.qa_score,
                "status": ReviewStatus.PENDING_REVIEW.value,
                "priority": request.priority.value,
                "submitted_at": request.submitted_at.isoformat(),
                "review_deadline": request.review_deadline.isoformat(),
                "review_notes": request.review_notes
            }
            
            async with self.session.post(
                f"{self.supabase_url}/rest/v1/admin_reviews",
                headers=headers,
                json=data
            ) as response:
                if response.status in [200, 201]:
                    logger.info(f"Review request stored for {request.product_name}")
                else:
                    logger.error(f"Failed to store review request: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error storing review request: {str(e)}")
    
    async def _notify_admins_new_review(self, request: ReviewRequest):
        """Notify admins about new review request"""
        notification = {
            "type": "new_review_request",
            "product_id": request.product_id,
            "product_name": request.product_name,
            "priority": request.priority.value,
            "qa_score": request.qa_score,
            "deadline": request.review_deadline.isoformat(),
            "message": f"New {request.priority.value} priority review: {request.product_name} (Score: {request.qa_score:.1f})"
        }
        
        # Store notification
        try:
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "title": f"Review Required: {request.product_name}",
                "content": json.dumps(notification),
                "role": "admin",
                "memory_type": "notification",
                "tags": ["review", "admin", request.priority.value],
                "meta_data": notification,
                "is_active": True
            }
            
            async with self.session.post(
                f"{self.supabase_url}/rest/v1/copilot_messages",
                headers=headers,
                json=data
            ) as response:
                if response.status in [200, 201]:
                    logger.info(f"Admin notification sent for {request.product_name}")
                    
        except Exception as e:
            logger.error(f"Error sending admin notification: {str(e)}")
    
    async def get_pending_reviews(self, reviewer: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all pending reviews, optionally filtered by reviewer"""
        try:
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}"
            }
            
            query = f"{self.supabase_url}/rest/v1/admin_reviews?status=eq.{ReviewStatus.PENDING_REVIEW.value}"
            if reviewer:
                query += f"&reviewer=eq.{reviewer}"
            query += "&order=priority.asc,review_deadline.asc"
            
            async with self.session.get(query, headers=headers) as response:
                if response.status == 200:
                    reviews = await response.json()
                    return reviews
                else:
                    logger.error(f"Failed to fetch pending reviews: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching pending reviews: {str(e)}")
            return []
    
    async def submit_review_decision(self, product_id: str, reviewer: str, 
                                   status: ReviewStatus, comments: str,
                                   required_changes: List[str] = None) -> ReviewDecision:
        """Submit an admin's review decision"""
        decision = ReviewDecision(
            review_id=f"rev_{product_id}_{datetime.utcnow().timestamp()}",
            product_id=product_id,
            status=status,
            reviewer=reviewer,
            reviewed_at=datetime.utcnow(),
            comments=comments,
            required_changes=required_changes or [],
            approval_conditions=self._generate_approval_conditions(status)
        )
        
        # Store decision
        await self._store_review_decision(decision)
        
        # Update product status
        if status == ReviewStatus.APPROVED:
            await self._update_product_status(product_id, 'active')
            await self._notify_product_approved(product_id)
        elif status == ReviewStatus.REJECTED:
            await self._update_product_status(product_id, 'rejected')
            await self._trigger_improvement_workflow(product_id, decision)
        elif status == ReviewStatus.REVISION_REQUESTED:
            await self._update_product_status(product_id, 'revision_needed')
            await self._create_revision_tasks(product_id, decision)
        
        return decision
    
    def _generate_approval_conditions(self, status: ReviewStatus) -> List[str]:
        """Generate approval conditions based on status"""
        if status == ReviewStatus.APPROVED:
            return [
                "Product meets all quality standards",
                "Ready for marketplace listing",
                "Monitor initial customer feedback"
            ]
        elif status == ReviewStatus.REVISION_REQUESTED:
            return [
                "Complete all requested changes",
                "Re-submit for review",
                "Address all identified issues"
            ]
        else:
            return []
    
    async def _store_review_decision(self, decision: ReviewDecision):
        """Store review decision in database"""
        try:
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json"
            }
            
            # Update review record
            async with self.session.patch(
                f"{self.supabase_url}/rest/v1/admin_reviews?product_id=eq.{decision.product_id}",
                headers=headers,
                json={
                    "status": decision.status.value,
                    "reviewer": decision.reviewer,
                    "reviewed_at": decision.reviewed_at.isoformat(),
                    "review_comments": decision.comments,
                    "required_changes": json.dumps(decision.required_changes)
                }
            ) as response:
                if response.status in [200, 204]:
                    logger.info(f"Review decision stored for product {decision.product_id}")
                    
            # Store decision in memory
            decision_data = {
                "title": f"Review Decision - {decision.product_id}",
                "content": json.dumps({
                    "review_id": decision.review_id,
                    "product_id": decision.product_id,
                    "status": decision.status.value,
                    "reviewer": decision.reviewer,
                    "reviewed_at": decision.reviewed_at.isoformat(),
                    "comments": decision.comments,
                    "required_changes": decision.required_changes,
                    "approval_conditions": decision.approval_conditions
                }),
                "role": "system",
                "memory_type": "review_decision",
                "tags": ["review", "decision", decision.status.value],
                "is_active": True
            }
            
            async with self.session.post(
                f"{self.supabase_url}/rest/v1/copilot_messages",
                headers=headers,
                json=decision_data
            ) as response:
                if response.status in [200, 201]:
                    logger.info("Review decision stored in memory")
                    
        except Exception as e:
            logger.error(f"Error storing review decision: {str(e)}")
    
    async def _update_product_status(self, product_id: str, status: str):
        """Update product status in marketplace"""
        try:
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json"
            }
            
            async with self.session.patch(
                f"{self.supabase_url}/rest/v1/marketplace_products?id=eq.{product_id}",
                headers=headers,
                json={
                    "status": status,
                    "last_reviewed": datetime.utcnow().isoformat()
                }
            ) as response:
                if response.status in [200, 204]:
                    logger.info(f"Product {product_id} status updated to {status}")
                    
        except Exception as e:
            logger.error(f"Error updating product status: {str(e)}")
    
    async def _notify_product_approved(self, product_id: str):
        """Send notification when product is approved"""
        logger.info(f"Product {product_id} approved and live in marketplace")
        # Additional notification logic here
    
    async def _trigger_improvement_workflow(self, product_id: str, decision: ReviewDecision):
        """Trigger improvement workflow for rejected products"""
        improvement_task = {
            "product_id": product_id,
            "reason": "admin_rejection",
            "review_comments": decision.comments,
            "required_changes": decision.required_changes,
            "priority": "high"
        }
        
        # Store improvement task
        try:
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "title": f"Improvement Required - Product {product_id}",
                "content": json.dumps(improvement_task),
                "role": "system",
                "memory_type": "improvement_task",
                "tags": ["improvement", "admin_requested", "high_priority"],
                "is_active": True
            }
            
            async with self.session.post(
                f"{self.supabase_url}/rest/v1/copilot_messages",
                headers=headers,
                json=data
            ) as response:
                if response.status in [200, 201]:
                    logger.info(f"Improvement task created for rejected product {product_id}")
                    
        except Exception as e:
            logger.error(f"Error creating improvement task: {str(e)}")
    
    async def _create_revision_tasks(self, product_id: str, decision: ReviewDecision):
        """Create specific revision tasks based on admin feedback"""
        for i, change in enumerate(decision.required_changes):
            task = {
                "product_id": product_id,
                "task_type": "revision",
                "description": change,
                "priority": "high",
                "created_by": decision.reviewer,
                "due_date": (datetime.utcnow() + timedelta(days=3)).isoformat()
            }
            
            # Store each revision task
            try:
                headers = {
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "title": f"Revision Task {i+1} - {product_id}",
                    "content": json.dumps(task),
                    "role": "system",
                    "memory_type": "revision_task",
                    "tags": ["revision", "task", "admin_requested"],
                    "is_active": True
                }
                
                async with self.session.post(
                    f"{self.supabase_url}/rest/v1/copilot_messages",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status in [200, 201]:
                        logger.info(f"Revision task created: {change}")
                        
            except Exception as e:
                logger.error(f"Error creating revision task: {str(e)}")
    
    async def check_review_sla(self):
        """Check for reviews exceeding SLA and escalate"""
        try:
            pending_reviews = await self.get_pending_reviews()
            
            for review in pending_reviews:
                deadline = datetime.fromisoformat(review['review_deadline'])
                if datetime.utcnow() > deadline:
                    logger.warning(f"Review SLA exceeded for {review['product_name']}")
                    await self._escalate_overdue_review(review)
                    
        except Exception as e:
            logger.error(f"Error checking review SLA: {str(e)}")
    
    async def _escalate_overdue_review(self, review: Dict[str, Any]):
        """Escalate overdue reviews"""
        escalation = {
            "type": "overdue_review",
            "product_id": review['product_id'],
            "product_name": review['product_name'],
            "overdue_by": (datetime.utcnow() - datetime.fromisoformat(review['review_deadline'])).total_seconds() / 3600,
            "original_priority": review['priority'],
            "escalated_to": "urgent"
        }
        
        # Update priority to urgent
        try:
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json"
            }
            
            async with self.session.patch(
                f"{self.supabase_url}/rest/v1/admin_reviews?product_id=eq.{review['product_id']}",
                headers=headers,
                json={"priority": ReviewPriority.URGENT.value}
            ) as response:
                if response.status in [200, 204]:
                    logger.info(f"Review escalated to urgent for {review['product_name']}")
                    
        except Exception as e:
            logger.error(f"Error escalating review: {str(e)}")
    
    async def generate_review_dashboard(self) -> Dict[str, Any]:
        """Generate admin review dashboard data"""
        try:
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}"
            }
            
            # Get review statistics
            async with self.session.get(
                f"{self.supabase_url}/rest/v1/admin_reviews",
                headers=headers
            ) as response:
                if response.status == 200:
                    all_reviews = await response.json()
                    
                    # Calculate statistics
                    total_reviews = len(all_reviews)
                    pending = sum(1 for r in all_reviews if r['status'] == ReviewStatus.PENDING_REVIEW.value)
                    approved = sum(1 for r in all_reviews if r['status'] == ReviewStatus.APPROVED.value)
                    rejected = sum(1 for r in all_reviews if r['status'] == ReviewStatus.REJECTED.value)
                    auto_approved = sum(1 for r in all_reviews if r['status'] == ReviewStatus.AUTO_APPROVED.value)
                    
                    # Calculate average review time
                    completed_reviews = [r for r in all_reviews if r.get('reviewed_at')]
                    if completed_reviews:
                        avg_review_time = sum(
                            (datetime.fromisoformat(r['reviewed_at']) - 
                             datetime.fromisoformat(r['submitted_at'])).total_seconds() / 3600
                            for r in completed_reviews
                        ) / len(completed_reviews)
                    else:
                        avg_review_time = 0
                    
                    dashboard = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "statistics": {
                            "total_reviews": total_reviews,
                            "pending": pending,
                            "approved": approved,
                            "rejected": rejected,
                            "auto_approved": auto_approved,
                            "approval_rate": (approved + auto_approved) / total_reviews * 100 if total_reviews > 0 else 0,
                            "avg_review_time_hours": round(avg_review_time, 1)
                        },
                        "pending_by_priority": {
                            "urgent": sum(1 for r in all_reviews if r['status'] == ReviewStatus.PENDING_REVIEW.value and r['priority'] == ReviewPriority.URGENT.value),
                            "high": sum(1 for r in all_reviews if r['status'] == ReviewStatus.PENDING_REVIEW.value and r['priority'] == ReviewPriority.HIGH.value),
                            "medium": sum(1 for r in all_reviews if r['status'] == ReviewStatus.PENDING_REVIEW.value and r['priority'] == ReviewPriority.MEDIUM.value),
                            "low": sum(1 for r in all_reviews if r['status'] == ReviewStatus.PENDING_REVIEW.value and r['priority'] == ReviewPriority.LOW.value)
                        }
                    }
                    
                    return dashboard
                    
        except Exception as e:
            logger.error(f"Error generating review dashboard: {str(e)}")
            return {}
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

async def main():
    """Main function"""
    workflow = AdminReviewWorkflow()
    
    try:
        await workflow.initialize()
        
        # Run continuous monitoring
        while True:
            # Check SLA compliance
            await workflow.check_review_sla()
            
            # Generate dashboard
            dashboard = await workflow.generate_review_dashboard()
            logger.info(f"Review Dashboard: {json.dumps(dashboard, indent=2)}")
            
            await asyncio.sleep(300)  # Check every 5 minutes
            
    except KeyboardInterrupt:
        logger.info("Shutting down admin review workflow")
    finally:
        await workflow.cleanup()

if __name__ == "__main__":
    asyncio.run(main())