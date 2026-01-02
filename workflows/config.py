"""
LangGraph Workflow Configuration
Centralized configuration for all workflows
"""
import os
from langchain_anthropic import ChatAnthropic

class WorkflowConfig:
    """Central configuration for all LangGraph workflows"""

    # Production URLs
    WEATHERCRAFT_API = "https://weathercraft-erp.vercel.app"
    BRAINOPS_BACKEND = "https://brainops-backend-prod.onrender.com"
    BRAINOPS_AGENTS = "https://brainops-ai-agents.onrender.com"

    # Database connection (uses existing db_pool from main.py)
    SUPABASE_URL = os.getenv("SUPABASE_URL")

    # Anthropic API for LLM reasoning
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

    # LLM for workflow reasoning (Claude Sonnet 4)
    @classmethod
    def get_llm(cls):
        """Get configured LLM instance"""
        if cls.ANTHROPIC_API_KEY:
            return ChatAnthropic(
                model="claude-sonnet-4",
                temperature=0,
                api_key=cls.ANTHROPIC_API_KEY
            )
        return None

    # Workflow timeouts
    WORKFLOW_TIMEOUT_SECONDS = 300  # 5 minutes
    STEP_TIMEOUT_SECONDS = 60  # 1 minute per step
    AGENT_TIMEOUT_SECONDS = 30  # 30 seconds per agent call
