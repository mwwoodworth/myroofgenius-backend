"""
Voice Commands System - Natural Language Control for WeatherCraft ERP
"Hey WeatherCraft, schedule Johnson repair tomorrow" → Action executed
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
import openai
import json
import logging
from typing import Dict, Any, List
import re
from datetime import datetime, timedelta
import asyncpg
# Optional speech recognition (would need pip install SpeechRecognition)
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None
import io
import os

router = APIRouter(prefix="/api/v1/voice", tags=["Voice Commands"])
logger = logging.getLogger(__name__)

from core.supabase_auth import get_authenticated_user

async def get_db_pool(request: Request) -> asyncpg.Pool:
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return pool

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

class VoiceCommandProcessor:
    """Processes natural language voice commands and converts them to actions"""

    def __init__(self):
        self.command_patterns = {
            "schedule": r"schedule\s+(.+?)\s+(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}\/\d{1,2})",
            "show": r"show\s+(.+)",
            "create": r"create\s+(.+)",
            "update": r"update\s+(.+)",
            "send": r"send\s+(.+?)\s+to\s+(.+)",
            "call": r"call\s+(.+)",
            "revenue": r"(?:revenue|profit|earnings|money)",
            "weather": r"weather",
            "jobs": r"jobs?\s+(today|this\s+week|active|completed)",
            "customer": r"customer\s+(.+)"
        }

    async def process_command(self, command_text: str, user_id: str, conn: asyncpg.Connection, tenant_id: str) -> Dict[str, Any]:
        """Process voice command and return actionable response"""

        command_lower = command_text.lower().strip()
        logger.info(f"Processing voice command: {command_text}")

        # Use GPT-4 to understand intent and extract parameters
        intent_response = await self.analyze_command_intent(command_text)

        if intent_response["confidence"] < 0.7:
            return {
                "success": False,
                "message": "I didn't understand that command. Please try again.",
                "suggestion": "Try commands like 'Show today's revenue' or 'Schedule Johnson repair tomorrow'"
            }

        # Execute the command based on intent
        result = await self.execute_command(intent_response, user_id, conn, tenant_id)
        return result

    async def analyze_command_intent(self, command_text: str) -> Dict[str, Any]:
        """Use GPT-4 to analyze voice command intent"""

        analysis_prompt = f"""
        Analyze this voice command for a roofing ERP system and extract:

        1. INTENT: What action should be performed?
        2. ENTITY: What object/person is being referenced?
        3. PARAMETERS: When, where, how much, etc.
        4. CONFIDENCE: How confident are you in this interpretation (0-1)?

        Voice command: "{command_text}"

        Possible intents:
        - SCHEDULE (schedule work, appointments, calls)
        - SHOW (display data, reports, information)
        - CREATE (new estimate, job, customer)
        - UPDATE (change status, modify data)
        - SEND (send invoice, email, text)
        - CALL (call customer, crew member)
        - WEATHER (check weather, weather alerts)

        Respond in JSON format with intent, entity, parameters, and confidence.
        """

        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=500,
                temperature=0.2
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            logger.error(f"Intent analysis error: {e}")
            return {
                "intent": "UNKNOWN",
                "entity": None,
                "parameters": {},
                "confidence": 0.0
            }

    async def execute_command(
        self,
        intent_data: Dict[str, Any],
        user_id: str,
        conn: asyncpg.Connection,
        tenant_id: str,
    ) -> Dict[str, Any]:
        """Execute the command based on analyzed intent"""

        intent = intent_data.get("intent", "").upper()
        entity = intent_data.get("entity", "")
        parameters = intent_data.get("parameters", {})

        try:
            if intent == "SCHEDULE":
                return await self.handle_schedule_command(entity, parameters, user_id, conn, tenant_id)

            elif intent == "SHOW":
                return await self.handle_show_command(entity, parameters, user_id, conn, tenant_id)

            elif intent == "CREATE":
                return await self.handle_create_command(entity, parameters, user_id, conn, tenant_id)

            elif intent == "SEND":
                return await self.handle_send_command(entity, parameters, user_id, conn, tenant_id)

            elif intent == "WEATHER":
                return await self.handle_weather_command(parameters, user_id, conn, tenant_id)

            else:
                return {
                    "success": False,
                    "message": f"I understand '{intent}' but can't execute it yet.",
                    "intent": intent,
                    "available_commands": ["schedule", "show", "create", "send", "weather"]
                }

        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return {
                "success": False,
                "message": "Failed to execute command",
                "error": str(e)
            }

    async def handle_schedule_command(
        self, entity: str, parameters: Dict, user_id: str, conn: asyncpg.Connection, tenant_id: str
    ):
        """Handle scheduling commands.

        NOTE: We do not fabricate side effects. If scheduling tables are not available,
        return a clear "not enabled" response.
        """

        when = parameters.get("when", "tomorrow")
        time = parameters.get("time", "09:00")

        # Parse the scheduling request
        if "repair" in entity.lower():
            customer_name = parameters.get("customer", entity.replace("repair", "").strip())

            return {
                "success": False,
                "action": "SCHEDULE_REPAIR",
                "message": "Scheduling via voice commands is not enabled on this server",
                "details": {
                    "customer": customer_name,
                    "service_type": "repair",
                    "date": when,
                    "time": time
                },
                "next_steps": [],
                "available": False,
            }

        elif "estimate" in entity.lower():
            customer_name = parameters.get("customer", entity.replace("estimate", "").strip())

            return {
                "success": False,
                "action": "SCHEDULE_ESTIMATE",
                "message": "Scheduling via voice commands is not enabled on this server",
                "details": {
                    "customer": customer_name,
                    "service_type": "estimate",
                    "date": when
                },
                "available": False,
            }

        return {
            "success": False,
            "message": "Scheduling via voice commands is not enabled on this server",
            "requires_confirmation": False,
            "available": False,
        }

    async def handle_show_command(
        self, entity: str, parameters: Dict, user_id: str, conn: asyncpg.Connection, tenant_id: str
    ):
        """Handle show/display commands"""

        if "revenue" in entity.lower() or "profit" in entity.lower():
            period = parameters.get("period", "today")

            period_key = period.lower().strip()
            if period_key in {"today", "day"}:
                start_expr = "CURRENT_DATE"
            elif period_key in {"week", "this week"}:
                start_expr = "date_trunc('week', NOW())"
            elif period_key in {"month", "this month"}:
                start_expr = "date_trunc('month', NOW())"
            else:
                start_expr = "CURRENT_DATE"

            amount = await conn.fetchval(
                f"""
                SELECT COALESCE(SUM(COALESCE(total_amount, 0)), 0)
                FROM invoices
                WHERE tenant_id = $1
                  AND (status = 'paid' OR payment_status = 'paid')
                  AND created_at >= {start_expr}
                """,
                tenant_id,
            )

            jobs = await conn.fetchval(
                f"""
                SELECT COUNT(*)
                FROM jobs
                WHERE tenant_id = $1
                  AND status = 'completed'
                  AND COALESCE(completed_date, created_at) >= {start_expr}
                """,
                tenant_id,
            )

            data = {"amount": float(amount or 0), "jobs": int(jobs or 0)}

            return {
                "success": True,
                "action": "SHOW_REVENUE",
                "message": f"💰 {period.title()}'s revenue: ${data['amount']:,.2f} from {data['jobs']} jobs",
                "data": data,
                "visual": True  # Trigger dashboard display
            }

        elif "job" in entity.lower():
            status = parameters.get("status", "active")

            status_key = status.lower().strip()
            if status_key in {"active", "in_progress"}:
                where_clause = "status IN ('in_progress', 'scheduled')"
            elif status_key == "completed":
                where_clause = "status = 'completed'"
            elif status_key == "scheduled":
                where_clause = "status = 'scheduled'"
            else:
                where_clause = "TRUE"

            count = await conn.fetchval(
                f"SELECT COUNT(*) FROM jobs WHERE tenant_id = $1 AND {where_clause}",
                tenant_id,
            )

            return {
                "success": True,
                "action": "SHOW_JOBS",
                "message": f"📋 {status.title()} jobs: {int(count or 0)}",
                "data": {"count": int(count or 0), "status": status}
            }

        elif "weather" in entity.lower():
            return {
                "success": False,
                "action": "SHOW_WEATHER",
                "message": "Weather data is not configured on this server",
                "data": None,
                "available": False,
            }

        return {
            "success": True,
            "message": f"Showing: {entity}",
            "action": "SHOW_GENERIC"
        }

    async def handle_create_command(
        self, entity: str, parameters: Dict, user_id: str, conn: asyncpg.Connection, tenant_id: str
    ):
        """Handle create commands"""

        if "estimate" in entity.lower():
            customer = parameters.get("customer", "")

            return {
                "success": False,
                "action": "CREATE_ESTIMATE",
                "message": "Creating estimates via voice commands is not enabled on this server",
                "next_steps": [],
                "redirect": None,
                "available": False,
            }

        return {
            "success": False,
            "message": "Create actions via voice commands are not enabled on this server",
            "action": "CREATE_GENERIC",
            "available": False,
        }

    async def handle_send_command(
        self, entity: str, parameters: Dict, user_id: str, conn: asyncpg.Connection, tenant_id: str
    ):
        """Handle send commands"""

        recipient = parameters.get("recipient", "")

        if "invoice" in entity.lower():
            return {
                "success": False,
                "action": "SEND_INVOICE",
                "message": "Sending invoices via voice commands is not enabled on this server",
                "status": "not_enabled",
                "available": False,
            }

        return {
            "success": False,
            "message": "Send actions via voice commands are not enabled on this server",
            "action": "SEND_GENERIC",
            "available": False,
        }

    async def handle_weather_command(
        self, parameters: Dict, user_id: str, conn: asyncpg.Connection, tenant_id: str
    ):
        """Handle weather-related commands"""

        return {
            "success": False,
            "action": "WEATHER_CHECK",
            "message": "Weather data is not configured on this server",
            "data": None,
            "alerts": []
        }

# Initialize processor
voice_processor = VoiceCommandProcessor()

@router.post("/command/text")
async def process_text_command(
    request: Request,
    command: str,
    pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_authenticated_user),
):
    """
    🎤 PROCESS TEXT VOICE COMMAND
    Send text command: "Schedule Johnson repair tomorrow"
    """

    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    user_id = current_user.get("id", "anonymous")
    async with pool.acquire() as conn:
        result = await voice_processor.process_command(command, user_id, conn, tenant_id)

    return {
        "command_processed": command,
        "user_id": user_id,
        "result": result,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/command/audio")
async def process_audio_command(
    request: Request,
    audio_file: UploadFile = File(...),
    pool: asyncpg.Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_authenticated_user),
):
    """
    🎤 PROCESS AUDIO VOICE COMMAND
    Upload audio file with voice command
    """

    try:
        # Read audio file
        audio_data = await audio_file.read()

        if not SPEECH_RECOGNITION_AVAILABLE:
            raise HTTPException(
                status_code=501,
                detail="Audio transcription is not available (missing SpeechRecognition dependency)",
            )

        recognizer = sr.Recognizer()
        audio_bytes = io.BytesIO(audio_data)
        with sr.AudioFile(audio_bytes) as source:
            audio = recognizer.record(source)
        transcribed_text = recognizer.recognize_google(audio)

        # Process the transcribed command
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        user_id = current_user.get("id", "anonymous")
        async with pool.acquire() as conn:
            result = await voice_processor.process_command(transcribed_text, user_id, conn, tenant_id)

        return {
            "audio_processed": True,
            "transcription": transcribed_text,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")

@router.get("/commands/help")
async def get_voice_commands_help():
    """
    💡 VOICE COMMANDS HELP
    Get list of available voice commands
    """

    return {
        "available_commands": {
            "scheduling": [
                "Schedule Johnson repair tomorrow",
                "Schedule estimate for Smith on Friday",
                "Book inspection for next week"
            ],
            "information": [
                "Show today's revenue",
                "Show active jobs",
                "Show this week's profit",
                "Check weather"
            ],
            "actions": [
                "Create estimate for new customer",
                "Send invoice to Johnson",
                "Call crew chief"
            ],
            "shortcuts": [
                "Hey WeatherCraft, what's my revenue?",
                "WeatherCraft, show me today's jobs",
                "Schedule next available slot"
            ]
        },
        "tips": [
            "Speak clearly and include specific details",
            "Use customer names when available",
            "Specify dates/times for scheduling",
            "Try 'Hey WeatherCraft' as a wake word"
        ]
    }

@router.get("/commands/examples")
async def get_command_examples():
    """
    📝 VOICE COMMAND EXAMPLES
    Real examples of what you can say
    """

    return {
        "examples": [
            {
                "command": "Schedule Johnson repair tomorrow at 2 PM",
                "result": "✅ Repair scheduled for Johnson tomorrow at 2:00 PM"
            },
            {
                "command": "Show me this week's revenue",
                "result": "💰 This week's revenue: $85,000 from 24 jobs"
            },
            {
                "command": "Create estimate for new customer on Oak Street",
                "result": "📝 Opening new estimate form with Oak Street address"
            },
            {
                "command": "What's the weather like for roofing?",
                "result": "🌤️ Perfect conditions: 75°F, clear skies, light winds"
            }
        ]
    }
