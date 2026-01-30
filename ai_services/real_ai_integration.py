"""
REAL AI Integration Service for MyRoofGenius
Replaces all fake random data with actual AI capabilities
"""
import os
import base64
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
import json
from PIL import Image
import io
import numpy as np
import re

# Configure logging
logger = logging.getLogger(__name__)

class AIServiceError(RuntimeError):
    pass


class AIServiceNotConfiguredError(AIServiceError):
    pass


class AIProviderCallError(AIServiceError):
    pass


class RealAIService:
    """
    Real AI service that integrates with multiple AI providers
    No more fake data - this is the real deal
    """
    
    def __init__(self):
        # API Keys from environment
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        
        # API endpoints
        self.openai_url = "https://api.openai.com/v1"
        self.anthropic_url = "https://api.anthropic.com/v1"
        self.gemini_url = f"https://generativelanguage.googleapis.com/v1beta"
        
        # Initialize HTTP client
        self.client = httpx.AsyncClient(timeout=60.0)

    def _configured_providers(self) -> List[str]:
        providers: List[str] = []
        if self.openai_key:
            providers.append("openai")
        if self.anthropic_key:
            providers.append("anthropic")
        if self.gemini_key:
            providers.append("gemini")
        return providers

    def _require_provider(self) -> None:
        if not self._configured_providers():
            raise AIServiceNotConfiguredError(
                "No AI providers configured. Set OPENAI_API_KEY and/or ANTHROPIC_API_KEY and/or GEMINI_API_KEY."
            )

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Strict JSON extraction: never invent fields on parse failure."""
        if not text:
            raise AIProviderCallError("AI provider returned an empty response")

        try:
            return json.loads(text)
        except Exception:
            pass

        # Match the first JSON object anywhere in the response (handles code fences, prose, etc.).
        # NOTE: Use [\s\S] (not an over-escaped charclass) so we can match across newlines.
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise AIProviderCallError("AI provider response was not valid JSON")

        try:
            return json.loads(match.group(0))
        except Exception as exc:
            raise AIProviderCallError("AI provider response was not valid JSON") from exc
        
    async def analyze_roof_image(self, image_data: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze roof image using GPT-4 Vision or Claude 3 Vision
        Returns real AI analysis, not random data
        """
        self._require_provider()

        last_error: Exception | None = None
        for provider in ("openai", "anthropic", "gemini"):
            try:
                if provider == "openai" and self.openai_key:
                    return await self._analyze_with_gpt4_vision(image_data, metadata)
                if provider == "anthropic" and self.anthropic_key:
                    return await self._analyze_with_claude_vision(image_data, metadata)
                if provider == "gemini" and self.gemini_key:
                    return await self._analyze_with_gemini_vision(image_data, metadata)
            except Exception as exc:
                last_error = exc
                logger.error("%s vision call failed: %s", provider, exc)

        raise AIProviderCallError("All configured AI providers failed") from last_error
    
    async def _analyze_with_gpt4_vision(self, image_data: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze roof using OpenAI GPT-4 Vision"""
        
        prompt = """You are an expert roofing contractor and inspector. Analyze this roof image and provide:
        
        1. Roof type (e.g., asphalt shingle, tile, metal, flat)
        2. Condition score (0-100 where 100 is perfect)
        3. Age estimate in years
        4. Square footage estimate (if visible)
        5. Roof pitch estimate
        6. List all damage detected with:
           - Type of damage
           - Severity (minor/moderate/severe)
           - Location on roof
           - Estimated repair cost
        7. Total repair estimate
        8. Full replacement estimate
        9. Insurance claim potential (high/medium/low)
        10. Urgency level (immediate/soon/preventive/none)
        11. Weather impact assessment
        
        Provide response in JSON format with these exact keys:
        roof_type, condition_score, age_estimate, square_footage, pitch, damage_detected (array),
        total_repair_estimate, replacement_estimate, insurance_claim_potential, urgency_level, weather_impact
        """
        
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1500
        }
        
        response = await self.client.post(
            f"{self.openai_url}/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            analysis = self._extract_json(content)
            
            # Add metadata
            analysis['ai_provider'] = 'OpenAI GPT-4 Vision'
            analysis['analysis_id'] = f"ROOF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            return analysis
        else:
            raise AIProviderCallError(f"OpenAI API error: {response.status_code} - {response.text}")
    
    async def _analyze_with_claude_vision(self, image_data: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze roof using Anthropic Claude 3 Vision"""
        
        prompt = """Analyze this roof image as an expert roofing inspector. Provide detailed analysis including:
        roof type, condition (0-100), age, damage assessment, repair costs, and recommendations.
        Format response as JSON with keys: roof_type, condition_score, age_estimate, damage_detected, 
        total_repair_estimate, replacement_estimate, urgency_level"""
        
        headers = {
            "x-api-key": self.anthropic_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 1500,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        response = await self.client.post(
            f"{self.anthropic_url}/messages",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['content'][0]['text']
            
            analysis = self._extract_json(content)
            analysis['ai_provider'] = 'Claude 3 Vision'
            
            return analysis
        else:
            raise AIProviderCallError(f"Claude API error: {response.status_code} - {response.text}")
    
    async def _analyze_with_gemini_vision(self, image_data: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze roof using Google Gemini Vision"""
        
        prompt = """Analyze this roof image and provide: roof type, condition score (0-100), 
        age estimate, damage list, repair costs, urgency level. Return as JSON."""
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_data
                            }
                        }
                    ]
                }
            ]
        }
        
        response = await self.client.post(
            f"{self.gemini_url}/models/gemini-1.5-pro-vision-002:generateContent?key={self.gemini_key}",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['candidates'][0]['content']['parts'][0]['text']
            
            analysis = self._extract_json(content)
            analysis['ai_provider'] = 'Google Gemini Vision'
            
            return analysis
        else:
            raise AIProviderCallError(f"Gemini API error: {response.status_code} - {response.text}")
    
    async def score_lead(self, lead_data: Dict[str, Any], signals: List[str]) -> Dict[str, Any]:
        """
        Real AI-powered lead scoring using machine learning
        """
        self._require_provider()
        
        # Use LLM for intelligent lead scoring
        prompt = f"""Analyze this lead and provide a score (0-100) and conversion strategy:
        
        Lead Data: {json.dumps(lead_data)}
        Behavioral Signals: {', '.join(signals)}
        
        Consider: urgency, budget, decision-making authority, engagement level, fit score.
        
        Return JSON with: score, conversion_probability, strategy (priority, action, offer), insights"""
        
        last_error: Exception | None = None
        for provider in ("openai", "anthropic", "gemini"):
            try:
                if provider == "openai" and self.openai_key:
                    response = await self._call_openai_chat(prompt)
                elif provider == "anthropic" and self.anthropic_key:
                    response = await self._call_claude_chat(prompt)
                elif provider == "gemini" and self.gemini_key:
                    response = await self._call_gemini_chat(prompt)
                else:
                    continue

                result = self._extract_json(response)
                result["ai_provider"] = provider
                return result
            except Exception as exc:
                last_error = exc
                logger.error("%s lead scoring call failed: %s", provider, exc)

        raise AIProviderCallError("All configured AI providers failed") from last_error
    
    async def generate_content(self, topic: str, style: str = "professional") -> Dict[str, Any]:
        """Generate real marketing content using AI"""
        
        prompt = f"""Create compelling {style} marketing content about {topic} for a roofing company.
        Include: engaging title, 300-word article, call-to-action, SEO keywords, and social media posts.
        Format as JSON with keys: title, content, cta, seo_keywords, social_media"""

        self._require_provider()

        last_error: Exception | None = None
        for provider in ("openai", "anthropic", "gemini"):
            try:
                if provider == "openai" and self.openai_key:
                    response = await self._call_openai_chat(prompt)
                elif provider == "anthropic" and self.anthropic_key:
                    response = await self._call_claude_chat(prompt)
                elif provider == "gemini" and self.gemini_key:
                    response = await self._call_gemini_chat(prompt)
                else:
                    continue

                content = self._extract_json(response)
                content["generated_by"] = "AI"
                content["ai_provider"] = provider
                content["timestamp"] = datetime.now().isoformat()
                return content
            except Exception as exc:
                last_error = exc
                logger.error("%s content generation failed: %s", provider, exc)

        raise AIProviderCallError("All configured AI providers failed") from last_error
    
    async def _call_openai_chat(self, prompt: str) -> str:
        """Call OpenAI Chat API"""
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        
        response = await self.client.post(
            f"{self.openai_url}/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        raise Exception(f"OpenAI error: {response.status_code} - {response.text[:500]}")

    async def generate_json(self, prompt: str) -> Dict[str, Any]:
        """Generate a JSON response from an LLM provider (no local fallbacks)."""
        self._require_provider()

        last_error: Exception | None = None
        for provider in ("openai", "anthropic", "gemini"):
            try:
                if provider == "openai" and self.openai_key:
                    response = await self._call_openai_chat(prompt)
                elif provider == "anthropic" and self.anthropic_key:
                    response = await self._call_claude_chat(prompt)
                elif provider == "gemini" and self.gemini_key:
                    response = await self._call_gemini_chat(prompt)
                else:
                    continue

                result = self._extract_json(response)
                result["ai_provider"] = provider
                return result
            except Exception as exc:
                last_error = exc
                logger.error("%s JSON generation failed: %s", provider, exc)

        raise AIProviderCallError("All configured AI providers failed") from last_error
    
    async def _call_claude_chat(self, prompt: str) -> str:
        """Call Claude API"""
        headers = {
            "x-api-key": self.anthropic_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            # Use an actually-available model for this API key (see Anthropic /v1/models).
            "model": "claude-sonnet-4-5-20250929",
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = await self.client.post(
            f"{self.anthropic_url}/messages",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()['content'][0]['text']
        raise Exception(f"Claude error: {response.status_code} - {response.text[:500]}")
    
    async def _call_gemini_chat(self, prompt: str) -> str:
        """Call Gemini API"""
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        response = await self.client.post(
            f"{self.gemini_url}/models/gemini-2.0-flash:generateContent?key={self.gemini_key}",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        raise Exception(f"Gemini error: {response.status_code} - {response.text[:500]}")
    
    async def predict_churn(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Real churn prediction using AI analysis"""
        
        prompt = f"""Analyze this customer data and predict churn risk:
        {json.dumps(customer_data)}
        
        Return JSON with: risk_score (0-100), risk_factors, retention_strategy, predicted_ltv"""

        self._require_provider()

        if self.openai_key:
            response = await self._call_openai_chat(prompt)
            provider = "openai"
        elif self.anthropic_key:
            response = await self._call_claude_chat(prompt)
            provider = "anthropic"
        else:
            response = await self._call_gemini_chat(prompt)
            provider = "gemini"

        result = self._extract_json(response)
        result["ai_provider"] = provider
        return result
    
    async def optimize_revenue(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize revenue using AI-driven analysis
        Returns actionable revenue optimization strategies
        """
        prompt = (
            "You are a revenue optimization assistant for a roofing SaaS/ERP.\n\n"
            f"Business data:\n{json.dumps(business_data)}\n\n"
            "Return JSON with keys: pricing_strategy, upsell_opportunities, growth_tactics, "
            "revenue_potential, customer_segments, implementation_timeline, confidence_score."
        )
        result = await self.generate_json(prompt)
        result["success"] = True
        result["timestamp"] = datetime.now().isoformat()
        return result
    
    async def close(self):
        """Clean up resources"""
        await self.client.aclose()

# Global instance
ai_service = RealAIService()
