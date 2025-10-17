"""
Direct AI Implementation - No dependencies on ai_engine
Uses API keys directly from environment
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import json
from datetime import datetime
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ai-direct", tags=["AI Direct"])

class AIRequest(BaseModel):
    text: str
    provider: Optional[str] = "openai"  # openai, anthropic, gemini
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500

@router.post("/analyze")
async def analyze_with_ai(request: AIRequest):
    """Direct AI analysis using configured providers"""
    try:
        if request.provider == "openai":
            return await analyze_with_openai(request)
        elif request.provider == "anthropic":
            return await analyze_with_anthropic(request)
        elif request.provider == "gemini":
            return await analyze_with_gemini(request)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {request.provider}")
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def analyze_with_openai(request: AIRequest):
    """Use OpenAI API directly"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="OpenAI API key not configured")

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)

        model = request.model or "gpt-4o-mini"  # Use mini for speed and cost

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert analyzer. Analyze the text and return a JSON response with:
                    {
                        "sentiment": "positive/neutral/negative",
                        "confidence": 0.0-1.0,
                        "key_topics": ["topic1", "topic2", ...],
                        "summary": "brief summary",
                        "insights": ["insight1", "insight2", ...]
                    }"""
                },
                {"role": "user", "content": request.text}
            ],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        analysis = json.loads(content)

        return {
            "status": "success",
            "provider": "openai",
            "model": model,
            "analysis": analysis,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

async def analyze_with_anthropic(request: AIRequest):
    """Use Anthropic Claude API directly"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="Anthropic API key not configured")

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        model = request.model or "claude-3-5-sonnet-20241022"

        response = client.messages.create(
            model=model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            messages=[
                {
                    "role": "user",
                    "content": f"""Analyze this text and respond with ONLY a JSON object (no other text):
                    {{
                        "sentiment": "positive/neutral/negative",
                        "confidence": 0.0-1.0,
                        "key_topics": ["topic1", "topic2"],
                        "summary": "brief summary",
                        "insights": ["insight1", "insight2"]
                    }}

                    Text to analyze: {request.text}"""
                }
            ]
        )

        content = response.content[0].text
        # Try to extract JSON if Claude added extra text
        if "{" in content:
            json_start = content.index("{")
            json_end = content.rindex("}") + 1
            content = content[json_start:json_end]

        analysis = json.loads(content)

        return {
            "status": "success",
            "provider": "anthropic",
            "model": model,
            "analysis": analysis,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Anthropic error: {e}")
        raise HTTPException(status_code=500, detail=f"Anthropic API error: {str(e)}")

async def analyze_with_gemini(request: AIRequest):
    """Use Google Gemini API directly"""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="Gemini API key not configured")

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        const_model = request.model or 'gemini-1.5-flash-002'
        model = genai.GenerativeModel(const_model)

        prompt = f"""Analyze this text and respond with ONLY a JSON object:
        {{
            "sentiment": "positive/neutral/negative",
            "confidence": 0.0-1.0,
            "key_topics": ["topic1", "topic2"],
            "summary": "brief summary",
            "insights": ["insight1", "insight2"]
        }}

        Text: {request.text}"""

        response = model.generate_content(prompt)
        content = response.text

        # Extract JSON from response
        if "{" in content:
            json_start = content.index("{")
            json_end = content.rindex("}") + 1
            content = content[json_start:json_end]

        analysis = json.loads(content)

        return {
            "status": "success",
            "provider": "gemini",
            "model": const_model,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Gemini error: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")

@router.get("/providers")
async def list_providers():
    """List available AI providers and their status"""
    return {
        "providers": {
            "openai": {
                "configured": bool(os.getenv("OPENAI_API_KEY")),
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                "default": "gpt-4o-mini"
            },
            "anthropic": {
                "configured": bool(os.getenv("ANTHROPIC_API_KEY")),
                "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
                "default": "claude-3-5-sonnet-20241022"
            },
            "gemini": {
                "configured": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
                "models": ["gemini-1.5-flash-002", "gemini-1.5-pro-002"],
                "default": "gemini-1.5-flash-002"
            }
        },
        "timestamp": datetime.now().isoformat()
    }
