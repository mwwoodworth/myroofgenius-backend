"""
Advanced AI Orchestration with fallback chains and error handling
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import hashlib

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import google.generativeai as genai
from groq import AsyncGroq

from app.core.config import settings
from app.core.exceptions import AIProviderError, AIQuotaExceededError

logger = logging.getLogger(__name__)

class AIProvider:
    """Base AI Provider interface"""
    
    def __init__(self, name: str, priority: int = 0):
        self.name = name
        self.priority = priority
        self.is_available = True
        self.failure_count = 0
        self.last_failure = None
        
    async def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError
    
    def mark_failure(self):
        self.failure_count += 1
        self.last_failure = datetime.utcnow()
        if self.failure_count >= 3:
            self.is_available = False
            logger.warning(f"Provider {self.name} marked unavailable after {self.failure_count} failures")
    
    def reset(self):
        self.failure_count = 0
        self.is_available = True
        self.last_failure = None

class OpenAIProvider(AIProvider):
    """OpenAI GPT-4 Provider"""
    
    def __init__(self):
        super().__init__("OpenAI GPT-4", priority=1)
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        
    async def generate(self, prompt: str, **kwargs) -> str:
        if not self.client:
            raise AIProviderError("OpenAI API key not configured")
            
        try:
            response = await self.client.chat.completions.create(
                model=kwargs.get("model", "gpt-4-turbo-preview"),
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1000)
            )
            return response.choices[0].message.content
        except Exception as e:
            self.mark_failure()
            raise AIProviderError(f"OpenAI error: {str(e)}")

class AnthropicProvider(AIProvider):
    """Anthropic Claude Provider"""
    
    def __init__(self):
        super().__init__("Anthropic Claude", priority=2)
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None
        
    async def generate(self, prompt: str, **kwargs) -> str:
        if not self.client:
            raise AIProviderError("Anthropic API key not configured")
            
        try:
            response = await self.client.messages.create(
                model=kwargs.get("model", "claude-3-opus-20240229"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", 1000),
                temperature=kwargs.get("temperature", 0.7)
            )
            return response.content[0].text
        except Exception as e:
            self.mark_failure()
            raise AIProviderError(f"Anthropic error: {str(e)}")

class GoogleProvider(AIProvider):
    """Google Gemini Provider"""
    
    def __init__(self):
        super().__init__("Google Gemini", priority=3)
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
            
    async def generate(self, prompt: str, **kwargs) -> str:
        if not self.model:
            raise AIProviderError("Google API key not configured")
            
        try:
            # Google's SDK is synchronous, run in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.model.generate_content,
                prompt
            )
            return response.text
        except Exception as e:
            self.mark_failure()
            raise AIProviderError(f"Google error: {str(e)}")

class GroqProvider(AIProvider):
    """Groq LPU Provider for fast inference"""
    
    def __init__(self):
        super().__init__("Groq", priority=4)
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None
        
    async def generate(self, prompt: str, **kwargs) -> str:
        if not self.client:
            raise AIProviderError("Groq API key not configured")
            
        try:
            response = await self.client.chat.completions.create(
                model=kwargs.get("model", "mixtral-8x7b-32768"),
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1000)
            )
            return response.choices[0].message.content
        except Exception as e:
            self.mark_failure()
            raise AIProviderError(f"Groq error: {str(e)}")

class AIOrchestrator:
    """
    Advanced AI Orchestrator with:
    - Multiple provider support
    - Automatic fallback chains
    - Caching and deduplication
    - Performance monitoring
    - Error recovery
    """
    
    def __init__(self):
        self.providers: List[AIProvider] = []
        self.cache = {}  # Simple in-memory cache
        self.metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "provider_usage": {},
            "errors": []
        }
        self._initialize_providers()
        
    def _initialize_providers(self):
        """Initialize available AI providers based on configuration"""
        
        if settings.OPENAI_API_KEY:
            self.providers.append(OpenAIProvider())
            
        if settings.ANTHROPIC_API_KEY:
            self.providers.append(AnthropicProvider())
            
        if settings.GOOGLE_API_KEY:
            self.providers.append(GoogleProvider())
            
        if settings.GROQ_API_KEY:
            self.providers.append(GroqProvider())
            
        # Sort by priority
        self.providers.sort(key=lambda x: x.priority)
        
        logger.info(f"Initialized {len(self.providers)} AI providers: {[p.name for p in self.providers]}")
    
    def _get_cache_key(self, prompt: str, **kwargs) -> str:
        """Generate cache key for request"""
        data = {"prompt": prompt, **kwargs}
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
    
    async def generate(
        self,
        prompt: str,
        use_cache: bool = True,
        fallback: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate AI response with automatic fallback
        
        Args:
            prompt: The input prompt
            use_cache: Whether to use caching
            fallback: Whether to use fallback providers
            **kwargs: Additional parameters for the AI model
            
        Returns:
            Dictionary with response and metadata
        """
        
        self.metrics["total_requests"] += 1
        
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(prompt, **kwargs)
            if cache_key in self.cache:
                self.metrics["cache_hits"] += 1
                logger.debug(f"Cache hit for prompt: {prompt[:50]}...")
                cached = self.cache[cache_key]
                cached["from_cache"] = True
                return cached
        
        # Try each provider in order
        errors = []
        for provider in self.providers:
            if not provider.is_available:
                continue
                
            try:
                logger.debug(f"Trying provider: {provider.name}")
                start_time = datetime.utcnow()
                
                response = await provider.generate(prompt, **kwargs)
                
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                
                # Update metrics
                if provider.name not in self.metrics["provider_usage"]:
                    self.metrics["provider_usage"][provider.name] = 0
                self.metrics["provider_usage"][provider.name] += 1
                
                # Reset provider on success
                provider.reset()
                
                result = {
                    "response": response,
                    "provider": provider.name,
                    "elapsed_time": elapsed,
                    "timestamp": datetime.utcnow().isoformat(),
                    "from_cache": False
                }
                
                # Cache successful response
                if use_cache:
                    self.cache[cache_key] = result
                    # Limit cache size
                    if len(self.cache) > 1000:
                        # Remove oldest entries
                        self.cache = dict(list(self.cache.items())[-500:])
                
                logger.info(f"Successfully generated response using {provider.name} in {elapsed:.2f}s")
                return result
                
            except AIProviderError as e:
                logger.warning(f"Provider {provider.name} failed: {str(e)}")
                errors.append({"provider": provider.name, "error": str(e)})
                
                if not fallback:
                    break
                    
                continue
        
        # All providers failed
        self.metrics["errors"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "prompt": prompt[:100],
            "errors": errors
        })
        
        # Keep only last 100 errors
        self.metrics["errors"] = self.metrics["errors"][-100:]
        
        raise AIProviderError(
            f"All AI providers failed. Errors: {json.dumps(errors, indent=2)}"
        )
    
    async def generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate with automatic retries"""
        
        for attempt in range(max_retries):
            try:
                return await self.generate(prompt, **kwargs)
            except AIProviderError as e:
                if attempt == max_retries - 1:
                    raise
                    
                # Wait before retry with exponential backoff
                await asyncio.sleep(2 ** attempt)
                
                # Reset some providers for retry
                for provider in self.providers:
                    if provider.failure_count < 3:
                        provider.is_available = True
        
        raise AIProviderError(f"Failed after {max_retries} retries")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator metrics"""
        available_providers = [p.name for p in self.providers if p.is_available]
        unavailable_providers = [p.name for p in self.providers if not p.is_available]
        
        return {
            **self.metrics,
            "available_providers": available_providers,
            "unavailable_providers": unavailable_providers,
            "cache_size": len(self.cache),
            "cache_hit_rate": (
                self.metrics["cache_hits"] / self.metrics["total_requests"] * 100
                if self.metrics["total_requests"] > 0 else 0
            )
        }
    
    def reset_all_providers(self):
        """Reset all providers to available state"""
        for provider in self.providers:
            provider.reset()
        logger.info("All AI providers reset to available state")

# Global orchestrator instance
ai_orchestrator = AIOrchestrator()