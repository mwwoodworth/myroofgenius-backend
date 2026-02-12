"""
BrainOps AI OS - Reasoning Engine

Provides sophisticated reasoning capabilities:
- Chain-of-thought reasoning
- Multi-step problem decomposition
- Causal reasoning
- Counterfactual analysis
- Decision analysis with confidence scoring
- Knowledge graph traversal
"""

import asyncio
import json
import logging
import uuid
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass, field
import asyncpg

from ._resilience import ResilientSubsystem

if TYPE_CHECKING:
    from .metacognitive_controller import MetacognitiveController

logger = logging.getLogger(__name__)


class ReasoningType(str, Enum):
    """Types of reasoning"""
    DEDUCTIVE = "deductive"       # From general to specific
    INDUCTIVE = "inductive"       # From specific to general
    ABDUCTIVE = "abductive"       # Best explanation
    CAUSAL = "causal"             # Cause and effect
    ANALOGICAL = "analogical"     # By comparison


@dataclass
class ReasoningStep:
    """A step in a reasoning chain"""
    step_number: int
    description: str
    conclusion: str
    confidence: float
    evidence: List[str]
    assumptions: List[str]


@dataclass
class ReasoningResult:
    """Result of a reasoning process"""
    id: str
    query: str
    reasoning_type: ReasoningType
    steps: List[ReasoningStep]
    final_conclusion: str
    confidence: float
    alternatives: List[Dict[str, Any]]
    created_at: datetime = field(default_factory=datetime.now)


class ReasoningEngine(ResilientSubsystem):
    """
    Reasoning Engine for BrainOps AI OS

    Provides:
    1. Chain-of-thought reasoning for complex problems
    2. Multi-step decision analysis
    3. Goal decomposition
    4. Causal analysis
    5. Revenue impact analysis
    """

    def __init__(self, controller: "MetacognitiveController"):
        self.controller = controller
        self.db_pool: Optional[asyncpg.Pool] = None

        # AI client
        self._openai_client = None
        self._anthropic_client = None
        self._openai_key = os.getenv("OPENAI_API_KEY")
        self._anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        # Reasoning cache
        self.reasoning_cache: Dict[str, ReasoningResult] = {}

        # Background tasks
        self._tasks: List[asyncio.Task] = []
        self._shutdown = asyncio.Event()

        # Metrics
        self.metrics = {
            "reasoning_requests": 0,
            "decisions_made": 0,
            "goals_decomposed": 0,
            "cache_hits": 0,
        }

    async def initialize(self, db_pool: asyncpg.Pool):
        """Initialize the reasoning engine"""
        self.db_pool = db_pool

        # Initialize AI clients
        if self._openai_key:
            import openai
            self._openai_client = openai.AsyncOpenAI(api_key=self._openai_key)

        if self._anthropic_key:
            import anthropic
            self._anthropic_client = anthropic.AsyncAnthropic(api_key=self._anthropic_key)

        try:
            await self._initialize_database()
        except Exception as e:
            if "permission denied" in str(e).lower():
                pass
            else:
                raise

        logger.info("ReasoningEngine initialized")

    async def _initialize_database(self):
        """Create required database tables"""
        await self._db_execute_with_retry('''
            -- Reasoning results
            CREATE TABLE IF NOT EXISTS brainops_reasoning (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                reasoning_id VARCHAR(50) UNIQUE NOT NULL,
                query TEXT NOT NULL,
                reasoning_type VARCHAR(50),
                steps JSONB,
                final_conclusion TEXT,
                confidence FLOAT,
                alternatives JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_reasoning_type
                ON brainops_reasoning(reasoning_type);

            -- Decision analysis
            CREATE TABLE IF NOT EXISTS brainops_decision_analysis (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                decision_id VARCHAR(50) UNIQUE NOT NULL,
                context JSONB,
                options JSONB,
                analysis JSONB,
                recommendation JSONB,
                confidence FLOAT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        ''')

    # =========================================================================
    # CHAIN OF THOUGHT REASONING
    # =========================================================================

    async def reason(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        reasoning_type: ReasoningType = ReasoningType.DEDUCTIVE
    ) -> ReasoningResult:
        """
        Perform chain-of-thought reasoning on a query.

        Args:
            query: The question or problem to reason about
            context: Additional context
            reasoning_type: Type of reasoning to apply

        Returns:
            ReasoningResult with steps and conclusion
        """
        self.metrics["reasoning_requests"] += 1

        # Check cache
        cache_key = f"{query}_{reasoning_type.value}"
        if cache_key in self.reasoning_cache:
            self.metrics["cache_hits"] += 1
            return self.reasoning_cache[cache_key]

        # Build reasoning prompt
        prompt = self._build_reasoning_prompt(query, context, reasoning_type)

        # Get AI response
        response = await self._call_ai(prompt)

        # Parse response into steps
        steps = self._parse_reasoning_steps(response)

        # Create result
        result = ReasoningResult(
            id=str(uuid.uuid4()),
            query=query,
            reasoning_type=reasoning_type,
            steps=steps,
            final_conclusion=steps[-1].conclusion if steps else "",
            confidence=self._calculate_confidence(steps),
            alternatives=[],
        )

        # Store in cache and database
        self.reasoning_cache[cache_key] = result
        await self._store_reasoning(result)

        return result

    def _build_reasoning_prompt(
        self,
        query: str,
        context: Optional[Dict[str, Any]],
        reasoning_type: ReasoningType
    ) -> str:
        """Build a prompt for chain-of-thought reasoning"""
        type_instructions = {
            ReasoningType.DEDUCTIVE: "Use deductive reasoning: start from general principles and derive specific conclusions.",
            ReasoningType.INDUCTIVE: "Use inductive reasoning: identify patterns from specific observations to form general conclusions.",
            ReasoningType.ABDUCTIVE: "Use abductive reasoning: find the most likely explanation for the observations.",
            ReasoningType.CAUSAL: "Use causal reasoning: identify cause-and-effect relationships.",
            ReasoningType.ANALOGICAL: "Use analogical reasoning: draw conclusions by comparing similar situations.",
        }

        context_str = f"\n\nContext:\n{json.dumps(context, indent=2)}" if context else ""

        return f"""You are a sophisticated reasoning engine. {type_instructions.get(reasoning_type, '')}

Query: {query}
{context_str}

Think through this step-by-step:

1. First, identify the key elements of the problem
2. Then, apply logical reasoning to connect the elements
3. Consider potential alternatives or counterarguments
4. Finally, state your conclusion with confidence level

Format your response as:
STEP 1: [Description]
CONCLUSION: [What we can conclude]
CONFIDENCE: [0-1]
EVIDENCE: [Supporting evidence]

STEP 2: ...

FINAL CONCLUSION: [Your overall conclusion]
OVERALL CONFIDENCE: [0-1]
"""

    def _parse_reasoning_steps(self, response: str) -> List[ReasoningStep]:
        """Parse AI response into reasoning steps"""
        steps = []
        lines = response.split('\n')

        current_step = None
        step_num = 0

        for line in lines:
            line = line.strip()

            if line.startswith('STEP'):
                step_num += 1
                current_step = {
                    'step_number': step_num,
                    'description': line.split(':', 1)[1].strip() if ':' in line else '',
                    'conclusion': '',
                    'confidence': 0.5,
                    'evidence': [],
                    'assumptions': [],
                }

            elif line.startswith('CONCLUSION:') and current_step:
                current_step['conclusion'] = line.split(':', 1)[1].strip()

            elif line.startswith('CONFIDENCE:') and current_step:
                try:
                    current_step['confidence'] = float(line.split(':', 1)[1].strip())
                except:
                    pass

            elif line.startswith('EVIDENCE:') and current_step:
                current_step['evidence'].append(line.split(':', 1)[1].strip())

            elif line.startswith('FINAL CONCLUSION:'):
                if current_step:
                    steps.append(ReasoningStep(**current_step))
                # Create final step
                steps.append(ReasoningStep(
                    step_number=step_num + 1,
                    description="Final synthesis",
                    conclusion=line.split(':', 1)[1].strip(),
                    confidence=0.8,
                    evidence=[],
                    assumptions=[],
                ))

            elif current_step and not line.startswith(('STEP', 'CONCLUSION', 'CONFIDENCE', 'EVIDENCE', 'OVERALL')):
                if line and current_step['description']:
                    current_step['description'] += ' ' + line

        # Add last step if not added
        if current_step and (not steps or steps[-1].step_number != step_num):
            steps.append(ReasoningStep(**current_step))

        # If no steps parsed, create a simple one
        if not steps:
            steps.append(ReasoningStep(
                step_number=1,
                description="Direct analysis",
                conclusion=response[:500],
                confidence=0.5,
                evidence=[],
                assumptions=[],
            ))

        return steps

    def _calculate_confidence(self, steps: List[ReasoningStep]) -> float:
        """Calculate overall confidence from steps"""
        if not steps:
            return 0.5

        # Average confidence, weighted toward later steps
        total_weight = 0
        weighted_sum = 0

        for i, step in enumerate(steps):
            weight = i + 1  # Later steps have more weight
            weighted_sum += step.confidence * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.5

    # =========================================================================
    # DECISION MAKING
    # =========================================================================

    async def make_decision(
        self,
        context: Dict[str, Any],
        options: List[Any],
        constraints: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Make a decision based on context and options.

        Args:
            context: Decision context
            options: Available options
            constraints: Any constraints to consider

        Returns:
            Decision result with reasoning
        """
        self.metrics["decisions_made"] += 1

        prompt = f"""You are a decision-making system. Analyze the following and recommend the best option.

Context:
{json.dumps(context, indent=2)}

Available Options:
{json.dumps(options, indent=2)}

Constraints:
{json.dumps(constraints or [], indent=2)}

For each option, analyze:
1. Pros and cons
2. Risk level (low/medium/high)
3. Expected outcome
4. Alignment with constraints

Then recommend the best option with confidence level (0-1).

Format:
OPTION 1 ANALYSIS:
Pros: [list]
Cons: [list]
Risk: [level]
Score: [0-1]

...

RECOMMENDATION: [option number or description]
CONFIDENCE: [0-1]
REASONING: [explanation]
"""

        response = await self._call_ai(prompt)

        # Parse response
        result = self._parse_decision_response(response, options)

        # Store decision
        decision_id = str(uuid.uuid4())
        await self._db_execute_with_retry('''
            INSERT INTO brainops_decision_analysis
            (decision_id, context, options, analysis, recommendation, confidence)
            VALUES ($1, $2, $3, $4, $5, $6)
        ''',
            decision_id,
            json.dumps(context),
            json.dumps(options),
            json.dumps(result.get('analysis', {})),
            json.dumps(result.get('selected_option', {})),
            result.get('confidence', 0.5))

        return result

    def _parse_decision_response(
        self,
        response: str,
        options: List[Any]
    ) -> Dict[str, Any]:
        """Parse decision response"""
        result = {
            "analysis": {},
            "selected_option": options[0] if options else None,
            "confidence": 0.5,
            "reasoning": "",
        }

        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('RECOMMENDATION:'):
                rec = line.split(':', 1)[1].strip()
                # Try to match to an option
                for i, opt in enumerate(options):
                    if str(i) in rec or str(i+1) in rec:
                        result["selected_option"] = opt
                        break
            elif line.startswith('CONFIDENCE:'):
                try:
                    result["confidence"] = float(line.split(':', 1)[1].strip())
                except:
                    pass
            elif line.startswith('REASONING:'):
                result["reasoning"] = line.split(':', 1)[1].strip()

        return result

    # =========================================================================
    # GOAL DECOMPOSITION
    # =========================================================================

    async def decompose_goal(self, goal) -> List[Dict[str, Any]]:
        """
        Decompose a goal into subtasks.

        Args:
            goal: Goal object or dict

        Returns:
            List of subtask definitions
        """
        self.metrics["goals_decomposed"] += 1

        goal_dict = goal if isinstance(goal, dict) else {
            "title": goal.title,
            "description": goal.description,
            "level": goal.level.value,
            "deadline": goal.deadline.isoformat() if goal.deadline else None,
        }

        prompt = f"""Decompose this goal into actionable subtasks.

Goal:
{json.dumps(goal_dict, indent=2)}

Break this down into 3-7 specific, actionable subtasks. For each subtask provide:
- title: Clear action-oriented title
- description: Brief description
- priority: high/medium/low
- estimated_effort: small/medium/large
- dependencies: list of other subtask titles this depends on

Format as JSON array:
[
  {{"title": "...", "description": "...", "priority": "...", "estimated_effort": "...", "dependencies": []}},
  ...
]
"""

        response = await self._call_ai(prompt)

        # Parse JSON from response
        try:
            # Find JSON array in response
            start = response.find('[')
            end = response.rfind(']') + 1
            if start >= 0 and end > start:
                subtasks = json.loads(response[start:end])
                return subtasks
        except json.JSONDecodeError:
            pass

        # Fallback: create simple subtasks
        return [
            {"title": f"Subtask 1 for: {goal_dict.get('title', 'Goal')}", "priority": "medium"},
            {"title": f"Subtask 2 for: {goal_dict.get('title', 'Goal')}", "priority": "medium"},
            {"title": f"Subtask 3 for: {goal_dict.get('title', 'Goal')}", "priority": "medium"},
        ]

    # =========================================================================
    # REVENUE IMPACT ANALYSIS
    # =========================================================================

    async def analyze_revenue_impact(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze potential revenue impact of an alert/situation"""
        prompt = f"""Analyze the revenue impact of this situation:

{json.dumps(alert, indent=2)}

Provide:
1. Estimated immediate revenue impact ($)
2. Estimated long-term revenue impact ($)
3. Probability this will materialize (0-1)
4. Recommended actions to mitigate/capitalize
5. Priority level (critical/high/medium/low)

Format:
IMMEDIATE_IMPACT: $X
LONGTERM_IMPACT: $X
PROBABILITY: 0.X
PRIORITY: level
ACTIONS:
- action 1
- action 2
REASONING: explanation
"""

        response = await self._call_ai(prompt)

        # Parse response
        result = {
            "immediate_impact": 0,
            "longterm_impact": 0,
            "probability": 0.5,
            "priority": "medium",
            "actions": [],
            "reasoning": "",
        }

        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('IMMEDIATE_IMPACT:'):
                try:
                    result["immediate_impact"] = float(
                        line.split('$')[1].split()[0].replace(',', '')
                    )
                except:
                    pass
            elif line.startswith('LONGTERM_IMPACT:'):
                try:
                    result["longterm_impact"] = float(
                        line.split('$')[1].split()[0].replace(',', '')
                    )
                except:
                    pass
            elif line.startswith('PROBABILITY:'):
                try:
                    result["probability"] = float(line.split(':')[1].strip())
                except:
                    pass
            elif line.startswith('PRIORITY:'):
                result["priority"] = line.split(':')[1].strip().lower()
            elif line.startswith('- '):
                result["actions"].append(line[2:])
            elif line.startswith('REASONING:'):
                result["reasoning"] = line.split(':', 1)[1].strip()

        return result

    # =========================================================================
    # AI CALLING
    # =========================================================================

    async def _call_ai(self, prompt: str) -> str:
        """Call AI provider for reasoning"""
        # Try OpenAI first
        if self._openai_client:
            try:
                response = await self._openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=2000,
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"OpenAI call failed: {e}")

        # Fallback to Anthropic
        if self._anthropic_client:
            try:
                response = await self._anthropic_client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text
            except Exception as e:
                logger.warning(f"Anthropic call failed: {e}")

        # Final fallback
        return "Unable to process reasoning request - no AI provider available"

    async def _store_reasoning(self, result: ReasoningResult):
        """Store reasoning result in database"""
        await self._db_execute_with_retry('''
            INSERT INTO brainops_reasoning
            (reasoning_id, query, reasoning_type, steps, final_conclusion,
             confidence, alternatives)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        ''',
            result.id,
            result.query,
            result.reasoning_type.value,
            json.dumps([{
                'step_number': s.step_number,
                'description': s.description,
                'conclusion': s.conclusion,
                'confidence': s.confidence,
            } for s in result.steps]),
            result.final_conclusion,
            result.confidence,
            json.dumps(result.alternatives))

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    async def process_reasoning_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process reasoning request from controller"""
        request_type = request.get("type", "reason")

        if request_type == "reason":
            result = await self.reason(
                query=request.get("query", ""),
                context=request.get("context"),
                reasoning_type=ReasoningType(request.get("reasoning_type", "deductive")),
            )
            return {
                "status": "completed",
                "conclusion": result.final_conclusion,
                "confidence": result.confidence,
                "steps": len(result.steps),
            }

        elif request_type == "decide":
            result = await self.make_decision(
                context=request.get("context", {}),
                options=request.get("options", []),
                constraints=request.get("constraints"),
            )
            return result

        return {"status": "unknown_type"}

    async def get_health(self) -> Dict[str, Any]:
        """Get reasoning engine health"""
        has_ai = bool(self._openai_client or self._anthropic_client)

        return {
            "status": "healthy" if has_ai else "degraded",
            "score": 1.0 if has_ai else 0.5,
            "ai_available": has_ai,
            "cache_size": len(self.reasoning_cache),
            "metrics": self.metrics.copy(),
        }

    async def shutdown(self):
        """Shutdown the reasoning engine"""
        self._shutdown.set()
        logger.info("ReasoningEngine shutdown complete")


# Singleton
_reasoning_engine: Optional[ReasoningEngine] = None


def get_reasoning_engine() -> Optional[ReasoningEngine]:
    """Get the reasoning engine instance"""
    return _reasoning_engine
