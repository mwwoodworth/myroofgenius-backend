# PERSISTENT MEMORY MASTER DIRECTIVE
## The Living, Learning Business Brain

### CRITICAL MANDATE
**EVERY AI interaction, EVERY system event, EVERY decision, EVERY error, EVERY success MUST be stored in persistent memory.**

This is not just logging - this is building a living, learning, evolving business intelligence that gets smarter with every interaction.

## Core Principles

### 1. MEMORY FIRST, ALWAYS
```python
# WRONG - Old way
def process_request(data):
    result = do_something(data)
    return result

# RIGHT - Memory-first approach
async def process_request(data, db: Session):
    memory_service = MemoryService(db)
    
    # Store the intent
    await memory_service.create_memory(
        user_id="system",
        title=f"Request: {data.get('type')}",
        content=json.dumps(data),
        memory_type="request_intent",
        tags=["incoming", "learning"],
        meta_data={"timestamp": datetime.utcnow().isoformat()}
    )
    
    # Process with context from past memories
    similar_requests = await memory_service.search_memories(
        query=data.get('description'),
        memory_type="request_intent"
    )
    
    result = do_something_with_context(data, similar_requests)
    
    # Store the outcome
    await memory_service.create_memory(
        user_id="system",
        title=f"Result: {result.get('status')}",
        content=json.dumps({"request": data, "result": result}),
        memory_type="request_outcome",
        tags=["outcome", "learning", result.get('status')],
        meta_data={"duration_ms": elapsed_time}
    )
    
    return result
```

### 2. EVERY AI AGENT MUST REMEMBER

#### AUREA Executive
```python
# AUREA must store EVERY conversation turn
async def aurea_chat(message: str, session_id: str, db: Session):
    memory = MemoryService(db)
    
    # Store user intent with full context
    await memory.create_memory(
        user_id=session_id,
        title=f"AUREA Input: {message[:50]}",
        content=message,
        memory_type="aurea_conversation",
        tags=["aurea", "user_input", "executive_ai"],
        meta_data={
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "context_length": len(message)
        }
    )
    
    # Retrieve ALL relevant context
    context = await memory.get_context_window(
        user_id=session_id,
        window_size=50,  # Last 50 interactions
        include_similar=True  # AI-powered similarity search
    )
    
    # Generate response with FULL context
    response = await generate_with_memory(message, context)
    
    # Store AI response for learning
    await memory.create_memory(
        user_id=session_id,
        title=f"AUREA Response: {response[:50]}",
        content=response,
        memory_type="aurea_response",
        tags=["aurea", "ai_output", "executive_ai"],
        meta_data={
            "session_id": session_id,
            "model": "claude-3",
            "confidence": 0.95
        }
    )
```

#### LangGraph Processes
```python
# EVERY node in LangGraph must use memory
class MemoryAwareNode:
    def __init__(self, memory_service: MemoryService):
        self.memory = memory_service
    
    async def execute(self, state: dict):
        # Store node entry
        entry_memory = await self.memory.create_memory(
            user_id="langgraph",
            title=f"Node {self.name} Entry",
            content=json.dumps(state),
            memory_type="langgraph_node",
            tags=["langgraph", self.name, "entry"],
            meta_data={"node": self.name, "phase": "entry"}
        )
        
        # Get historical performance
        past_executions = await self.memory.search_memories(
            query=f"node:{self.name} outcome",
            limit=100
        )
        
        # Learn from past and execute
        result = await self.process_with_learning(state, past_executions)
        
        # Store outcome with learnings
        await self.memory.create_memory(
            user_id="langgraph",
            title=f"Node {self.name} Outcome",
            content=json.dumps({
                "input": state,
                "output": result,
                "learnings": self.extract_learnings(result, past_executions)
            }),
            memory_type="langgraph_outcome",
            tags=["langgraph", self.name, "outcome", "learning"],
            meta_data={
                "node": self.name,
                "success": result.get('success'),
                "duration_ms": result.get('duration')
            }
        )
```

### 3. SYSTEM-WIDE MEMORY PATTERNS

#### Error Learning
```python
# EVERY error becomes a learning opportunity
async def global_error_handler(error: Exception, context: dict, db: Session):
    memory = MemoryService(db)
    
    # Store error with FULL context
    error_memory = await memory.create_memory(
        user_id="system",
        title=f"Error: {type(error).__name__}",
        content=f"""
Error: {str(error)}
Traceback: {traceback.format_exc()}
Context: {json.dumps(context, indent=2)}
""",
        memory_type="system_error",
        tags=["error", type(error).__name__, "learning_opportunity"],
        meta_data={
            "error_type": type(error).__name__,
            "timestamp": datetime.utcnow().isoformat(),
            "context": context
        }
    )
    
    # Find similar errors and solutions
    similar_errors = await memory.search_memories(
        query=str(error),
        memory_type="system_error",
        limit=10
    )
    
    # If we've seen this before, apply known solutions
    solutions = await memory.search_memories(
        query=f"solution for {type(error).__name__}",
        memory_type="error_solution"
    )
    
    if solutions:
        # Apply automated fix
        await apply_solution(solutions[0], context)
        
        # Record successful resolution
        await memory.create_memory(
            user_id="system",
            title=f"Auto-resolved: {type(error).__name__}",
            content=f"Applied solution: {solutions[0].content}",
            memory_type="error_resolution",
            tags=["auto_fix", "success", "learning_applied"]
        )
```

#### Performance Optimization
```python
# EVERY request tracks performance for optimization
class MemoryOptimizedEndpoint:
    async def handle_request(self, request: Request, db: Session):
        memory = MemoryService(db)
        start_time = time.time()
        
        # Check if we've optimized this before
        endpoint_key = f"{request.method}:{request.url.path}"
        optimizations = await memory.search_memories(
            query=f"optimization:{endpoint_key}",
            memory_type="performance_optimization"
        )
        
        # Apply learned optimizations
        if optimizations:
            request = apply_optimizations(request, optimizations)
        
        # Process request
        result = await process(request)
        
        # Store performance data
        duration = (time.time() - start_time) * 1000
        await memory.create_memory(
            user_id="system",
            title=f"Performance: {endpoint_key}",
            content=json.dumps({
                "endpoint": endpoint_key,
                "duration_ms": duration,
                "optimizations_applied": len(optimizations)
            }),
            memory_type="performance_metric",
            tags=["performance", "endpoint", "monitoring"],
            meta_data={
                "duration_ms": duration,
                "endpoint": endpoint_key,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Learn if slow
        if duration > 1000:  # Slow request
            await self.analyze_and_learn(request, duration, memory)
```

### 4. MEMORY-DRIVEN DECISION MAKING

```python
class AIDecisionEngine:
    def __init__(self, memory_service: MemoryService):
        self.memory = memory_service
    
    async def make_decision(self, context: dict):
        # Get ALL relevant historical data
        historical_decisions = await self.memory.search_memories(
            query=json.dumps(context),
            memory_type="business_decision",
            limit=100
        )
        
        # Analyze outcomes of similar decisions
        successful_patterns = []
        failed_patterns = []
        
        for decision in historical_decisions:
            if decision.meta_data.get('outcome') == 'success':
                successful_patterns.append(decision)
            else:
                failed_patterns.append(decision)
        
        # Make informed decision
        decision = await self.generate_decision(
            context,
            successful_patterns,
            failed_patterns
        )
        
        # Store decision for future learning
        decision_memory = await self.memory.create_memory(
            user_id="ai_decision_engine",
            title=f"Decision: {decision['action']}",
            content=json.dumps({
                "context": context,
                "decision": decision,
                "historical_success_rate": len(successful_patterns) / len(historical_decisions) if historical_decisions else 0
            }),
            memory_type="business_decision",
            tags=["decision", "ai_driven", "learning"],
            meta_data={
                "confidence": decision['confidence'],
                "based_on_patterns": len(historical_decisions)
            }
        )
        
        # Set up tracking for outcome
        await self.schedule_outcome_tracking(decision_memory.id)
        
        return decision
```

### 5. CONTINUOUS LEARNING LOOPS

```python
class MemoryLearningEngine:
    """Runs continuously to extract insights from memory"""
    
    async def continuous_learning_loop(self, db: Session):
        memory = MemoryService(db)
        
        while True:
            # Analyze error patterns
            recent_errors = await memory.get_recent_memories(
                memory_type="system_error",
                hours=24
            )
            
            error_patterns = self.identify_patterns(recent_errors)
            for pattern in error_patterns:
                await memory.create_memory(
                    user_id="learning_engine",
                    title=f"Error Pattern Detected: {pattern['type']}",
                    content=json.dumps(pattern),
                    memory_type="ai_insight",
                    tags=["pattern", "error", "actionable"]
                )
            
            # Analyze performance trends
            performance_data = await memory.get_recent_memories(
                memory_type="performance_metric",
                hours=24
            )
            
            trends = self.identify_trends(performance_data)
            for trend in trends:
                await memory.create_memory(
                    user_id="learning_engine",
                    title=f"Performance Trend: {trend['direction']}",
                    content=json.dumps(trend),
                    memory_type="ai_insight",
                    tags=["trend", "performance", "predictive"]
                )
            
            # Generate daily learnings report
            await self.generate_daily_learnings(memory)
            
            # Sleep for next cycle
            await asyncio.sleep(300)  # Run every 5 minutes
```

## Implementation Checklist

### ✅ Backend Services
- [ ] AUREA Executive - Store EVERY conversation
- [ ] LangGraph - Memory at EVERY node
- [ ] API Endpoints - Track ALL requests/responses
- [ ] Error Handlers - Learn from EVERY error
- [ ] Background Tasks - Store ALL processing steps

### ✅ Frontend Integration
- [ ] User Actions - Track EVERY click/interaction
- [ ] Page Views - Store navigation patterns
- [ ] Form Submissions - Remember user preferences
- [ ] Error Boundaries - Learn from UI errors

### ✅ AI Agents
- [ ] Claude - Store ALL interactions
- [ ] GPT - Track ALL queries/responses
- [ ] Gemini - Remember ALL analyses
- [ ] Custom Agents - Memory-first architecture

### ✅ Business Logic
- [ ] Decisions - Record with full context
- [ ] Calculations - Store inputs/outputs
- [ ] Workflows - Track every step
- [ ] Automations - Learn and improve

## Memory Types Taxonomy

```python
MEMORY_TYPES = {
    # Conversations
    "aurea_conversation": "AUREA executive AI chats",
    "user_interaction": "General user interactions",
    "ai_response": "AI-generated responses",
    
    # System Events
    "system_error": "Errors with full context",
    "system_event": "Significant system events",
    "performance_metric": "Performance measurements",
    
    # Learning
    "ai_insight": "AI-discovered patterns",
    "error_solution": "Proven error fixes",
    "optimization": "Performance improvements",
    
    # Business
    "business_decision": "Business logic decisions",
    "calculation_result": "Computed outcomes",
    "workflow_state": "Process states",
    
    # Frontend
    "user_action": "User UI interactions",
    "page_view": "Navigation tracking",
    "ui_error": "Frontend errors",
    
    # External
    "api_call": "External API interactions",
    "webhook_event": "Incoming webhooks",
    "integration_sync": "Third-party syncs"
}
```

## The Vision

Every byte of data flowing through our system contributes to a growing, learning, evolving business brain that:

1. **Never forgets** - Every interaction is preserved
2. **Always learns** - Patterns emerge from data
3. **Continuously improves** - Apply learnings automatically
4. **Predicts issues** - See problems before they happen
5. **Optimizes itself** - Gets faster and smarter over time

This is not just a database - it's the foundation of an AI business that learns and grows autonomously.

## Next Steps

1. Audit EVERY function in the codebase
2. Add memory service to EVERY endpoint
3. Create memory hooks for EVERY AI interaction
4. Build continuous learning loops
5. Generate insights dashboards

The persistent memory system is our competitive advantage - the difference between a static application and a living, learning business intelligence.