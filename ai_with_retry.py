"""
AI Service with Retry Logic and Warm-up
Fixes timeout issues with exponential backoff
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import aiohttp
import logging
import time
import json
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["AI with Retry"])

# Cache for AI responses
response_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = 3600  # 1 hour

class AIRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 150
    temperature: Optional[float] = 0.7
    model: Optional[str] = "gpt-3.5-turbo"

class AIResponse(BaseModel):
    response: str
    provider: str
    cached: bool = False
    response_time: float
    retry_count: int = 0

async def call_ai_with_retry(
    prompt: str,
    max_tokens: int = 150,
    max_retries: int = 3,
    timeout: int = 60
) -> Dict[str, Any]:
    """
    Call AI service with exponential backoff retry
    """
    # Check cache first
    cache_key = f"{prompt}:{max_tokens}"
    if cache_key in response_cache:
        cached_response = response_cache[cache_key]
        if cached_response['expires'] > datetime.now():
            logger.info(f"Returning cached response for prompt: {prompt[:50]}...")
            return {
                "response": cached_response['response'],
                "provider": cached_response['provider'],
                "cached": True,
                "response_time": 0.01,
                "retry_count": 0
            }

    # Try different AI providers in sequence
    providers = [
        ("https://brainops-ai-agents.onrender.com/ai/generate", "brainops"),
        ("https://api.openai.com/v1/completions", "openai"),
        ("fallback", "fallback")
    ]

    for retry in range(max_retries):
        for provider_url, provider_name in providers:
            if provider_name == "fallback":
                # Use intelligent fallback
                return generate_fallback_response(prompt, max_tokens)

            try:
                start_time = time.time()

                async with aiohttp.ClientSession() as session:
                    # Prepare request based on provider
                    if provider_name == "brainops":
                        payload = {
                            "prompt": prompt,
                            "max_tokens": max_tokens
                        }
                    else:
                        payload = {
                            "model": "gpt-3.5-turbo",
                            "prompt": prompt,
                            "max_tokens": max_tokens,
                            "temperature": 0.7
                        }

                    # Make request with timeout
                    async with session.post(
                        provider_url,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            response_time = time.time() - start_time

                            # Extract response based on provider format
                            if provider_name == "brainops":
                                ai_response = data.get("response", "")
                            else:
                                ai_response = data.get("choices", [{}])[0].get("text", "")

                            # Cache the response
                            response_cache[cache_key] = {
                                "response": ai_response,
                                "provider": provider_name,
                                "expires": datetime.now() + timedelta(seconds=CACHE_TTL)
                            }

                            return {
                                "response": ai_response,
                                "provider": provider_name,
                                "cached": False,
                                "response_time": response_time,
                                "retry_count": retry
                            }

            except asyncio.TimeoutError:
                logger.warning(f"Timeout for {provider_name} (retry {retry + 1}/{max_retries})")
                if retry < max_retries - 1:
                    await asyncio.sleep(2 ** retry)  # Exponential backoff
                continue

            except Exception as e:
                logger.error(f"Error calling {provider_name}: {e}")
                continue

    # If all retries failed, use fallback
    return generate_fallback_response(prompt, max_tokens)

def generate_fallback_response(prompt: str, max_tokens: int) -> Dict[str, Any]:
    """
    Generate intelligent fallback response when AI is unavailable
    """
    prompt_lower = prompt.lower()

    # Roofing-specific responses
    if "metal roof" in prompt_lower:
        response = "Metal roofing offers excellent durability (40-70 years), energy efficiency, and weather resistance. It's lightweight, fire-resistant, and environmentally friendly. While initial costs are higher, long-term savings on maintenance and energy make it cost-effective."

    elif "estimate" in prompt_lower or "cost" in prompt_lower:
        response = "Roofing costs vary by material and size. Asphalt shingles: $3-5/sq ft. Metal: $5-12/sq ft. Tile: $7-15/sq ft. For accurate estimates, consider roof size, complexity, permits, and labor costs."

    elif "repair" in prompt_lower:
        response = "Common roof repairs include: shingle replacement ($150-400), flashing repair ($200-500), leak fixes ($300-1000). Regular inspections prevent major damage. Emergency repairs may cost 50% more."

    elif "maintenance" in prompt_lower:
        response = "Roof maintenance essentials: bi-annual inspections, gutter cleaning, debris removal, checking flashings, and addressing minor issues promptly. Professional inspection recommended annually."

    elif "warranty" in prompt_lower:
        response = "Roofing warranties typically include: manufacturer's material warranty (20-50 years) and contractor's workmanship warranty (5-10 years). Extended warranties available for premium materials."

    elif "insurance" in prompt_lower:
        response = "Most homeowner's insurance covers sudden roof damage from storms, fire, or falling objects. Gradual wear and improper maintenance typically aren't covered. Document all damage with photos."

    else:
        # Generic professional response
        response = "Thank you for your inquiry. Based on your question, I recommend consulting with our roofing specialists for detailed, personalized advice. Our team can provide specific recommendations based on your unique situation and requirements."

    return {
        "response": response[:max_tokens],
        "provider": "fallback",
        "cached": False,
        "response_time": 0.05,
        "retry_count": 0
    }

@router.post("/generate/retry", response_model=AIResponse)
async def generate_with_retry(request: AIRequest):
    """
    Generate AI response with retry logic
    """
    try:
        result = await call_ai_with_retry(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            max_retries=3,
            timeout=60
        )

        return AIResponse(**result)

    except Exception as e:
        logger.error(f"AI generation failed: {e}")
        # Return fallback
        fallback = generate_fallback_response(request.prompt, request.max_tokens)
        return AIResponse(**fallback)

@router.get("/warmup")
async def warmup():
    """
    Warm-up endpoint to prevent cold starts
    """
    return {
        "status": "warm",
        "timestamp": datetime.now().isoformat(),
        "cache_size": len(response_cache),
        "message": "AI service is warm and ready"
    }

@router.get("/cache/stats")
async def cache_stats():
    """
    Get cache statistics
    """
    valid_entries = sum(
        1 for v in response_cache.values()
        if v['expires'] > datetime.now()
    )

    return {
        "total_entries": len(response_cache),
        "valid_entries": valid_entries,
        "expired_entries": len(response_cache) - valid_entries,
        "cache_ttl_seconds": CACHE_TTL
    }

@router.delete("/cache/clear")
async def clear_cache():
    """
    Clear the response cache
    """
    count = len(response_cache)
    response_cache.clear()
    return {
        "cleared": count,
        "message": f"Cleared {count} cached responses"
    }