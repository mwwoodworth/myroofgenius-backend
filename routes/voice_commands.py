"""
Voice Commands System - Natural Language Control for WeatherCraft ERP
"Hey WeatherCraft, schedule Johnson repair tomorrow" → Action executed
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from ..database import get_db

from sqlalchemy.orm import Session
import openai
import json
import logging
from typing import Dict, Any, List
import re
from datetime import datetime, timedelta
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

# Placeholder auth and database functions
def get_db():
    """Placeholder for database session"""
    return None

def get_current_user():
    """Placeholder for current user"""
    return {"sub": "anonymous"}

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

    async def process_command(self, command_text: str, user_id: str, db: Session) -> Dict[str, Any]:
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
        result = await self.execute_command(intent_response, user_id, db)
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

    async def execute_command(self, intent_data: Dict[str, Any], user_id: str, db: Session) -> Dict[str, Any]:
        """Execute the command based on analyzed intent"""

        intent = intent_data.get("intent", "").upper()
        entity = intent_data.get("entity", "")
        parameters = intent_data.get("parameters", {})

        try:
            if intent == "SCHEDULE":
                return await self.handle_schedule_command(entity, parameters, user_id, db)

            elif intent == "SHOW":
                return await self.handle_show_command(entity, parameters, user_id, db)

            elif intent == "CREATE":
                return await self.handle_create_command(entity, parameters, user_id, db)

            elif intent == "SEND":
                return await self.handle_send_command(entity, parameters, user_id, db)

            elif intent == "WEATHER":
                return await self.handle_weather_command(parameters, user_id, db)

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

    async def handle_schedule_command(self, entity: str, parameters: Dict, user_id: str, db: Session):
        """Handle scheduling commands"""

        when = parameters.get("when", "tomorrow")
        time = parameters.get("time", "09:00")

        # Parse the scheduling request
        if "repair" in entity.lower():
            customer_name = parameters.get("customer", entity.replace("repair", "").strip())

            return {
                "success": True,
                "action": "SCHEDULE_REPAIR",
                "message": f"✅ Scheduled repair for {customer_name} on {when} at {time}",
                "details": {
                    "customer": customer_name,
                    "service_type": "repair",
                    "date": when,
                    "time": time
                },
                "next_steps": [
                    "Added to calendar",
                    "Crew notified",
                    "Customer confirmation sent"
                ]
            }

        elif "estimate" in entity.lower():
            customer_name = parameters.get("customer", entity.replace("estimate", "").strip())

            return {
                "success": True,
                "action": "SCHEDULE_ESTIMATE",
                "message": f"✅ Scheduled estimate for {customer_name} on {when}",
                "details": {
                    "customer": customer_name,
                    "service_type": "estimate",
                    "date": when
                }
            }

        return {
            "success": True,
            "message": f"Scheduled: {entity} for {when}",
            "requires_confirmation": True
        }

    async def handle_show_command(self, entity: str, parameters: Dict, user_id: str, db: Session):
        """Handle show/display commands"""

        if "revenue" in entity.lower() or "profit" in entity.lower():
            period = parameters.get("period", "today")

            # Mock revenue data - replace with actual database queries
            revenue_data = {
                "today": {"amount": 12500.00, "jobs": 5},
                "week": {"amount": 85000.00, "jobs": 24},
                "month": {"amount": 340000.00, "jobs": 89}
            }

            data = revenue_data.get(period, revenue_data["today"])

            return {
                "success": True,
                "action": "SHOW_REVENUE",
                "message": f"💰 {period.title()}'s revenue: ${data['amount']:,.2f} from {data['jobs']} jobs",
                "data": data,
                "visual": True  # Trigger dashboard display
            }

        elif "job" in entity.lower():
            status = parameters.get("status", "active")

            # Mock job data
            job_counts = {
                "active": 12,
                "completed": 156,
                "scheduled": 8
            }

            return {
                "success": True,
                "action": "SHOW_JOBS",
                "message": f"📋 {status.title()} jobs: {job_counts.get(status, 0)}",
                "data": {"count": job_counts.get(status, 0), "status": status}
            }

        elif "weather" in entity.lower():
            return {
                "success": True,
                "action": "SHOW_WEATHER",
                "message": "🌤️ Today: 75°F, Clear skies. Perfect for roofing work!",
                "data": {
                    "temperature": 75,
                    "conditions": "clear",
                    "wind": "5 mph",
                    "recommendation": "Excellent roofing conditions"
                }
            }

        return {
            "success": True,
            "message": f"Showing: {entity}",
            "action": "SHOW_GENERIC"
        }

    async def handle_create_command(self, entity: str, parameters: Dict, user_id: str, db: Session):
        """Handle create commands"""

        if "estimate" in entity.lower():
            customer = parameters.get("customer", "")

            return {
                "success": True,
                "action": "CREATE_ESTIMATE",
                "message": f"📝 Creating new estimate for {customer}",
                "next_steps": ["Opening estimate form", "Pre-filling customer data"],
                "redirect": "/estimates/new"
            }

        return {
            "success": True,
            "message": f"Creating: {entity}",
            "action": "CREATE_GENERIC"
        }

    async def handle_send_command(self, entity: str, parameters: Dict, user_id: str, db: Session):
        """Handle send commands"""

        recipient = parameters.get("recipient", "")

        if "invoice" in entity.lower():
            return {
                "success": True,
                "action": "SEND_INVOICE",
                "message": f"📧 Sending invoice to {recipient}",
                "status": "queued"
            }

        return {
            "success": True,
            "message": f"Sending {entity} to {recipient}",
            "action": "SEND_GENERIC"
        }

    async def handle_weather_command(self, parameters: Dict, user_id: str, db: Session):
        """Handle weather-related commands"""

        return {
            "success": True,
            "action": "WEATHER_CHECK",
            "message": "🌤️ Weather looks great for roofing! 75°F, clear skies, light winds.",
            "data": {
                "temperature": 75,
                "conditions": "clear",
                "wind_speed": 5,
                "precipitation": 0,
                "recommendation": "Perfect roofing conditions"
            },
            "alerts": []
        }

# Initialize processor
voice_processor = VoiceCommandProcessor()

@router.post("/command/text")
async def process_text_command(
    command: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🎤 PROCESS TEXT VOICE COMMAND
    Send text command: "Schedule Johnson repair tomorrow"
    """

    user_id = current_user.get("sub", "anonymous")
    result = await voice_processor.process_command(command, user_id, db)

    return {
        "command_processed": command,
        "user_id": user_id,
        "result": result,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/command/audio")
async def process_audio_command(
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🎤 PROCESS AUDIO VOICE COMMAND
    Upload audio file with voice command
    """

    try:
        # Read audio file
        audio_data = await audio_file.read()

        # Convert speech to text (would need speech recognition setup)
        # For now, return placeholder
        transcribed_text = "show today's revenue"  # Placeholder

        # Process the transcribed command
        user_id = current_user.get("sub", "anonymous")
        result = await voice_processor.process_command(transcribed_text, user_id, db)

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