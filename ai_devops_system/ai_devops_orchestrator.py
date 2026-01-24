#!/usr/bin/env python3
"""
AI DevOps Orchestrator
Main system that coordinates all AI DevOps components
"""

import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import argparse

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import our custom modules
from memory_system import PersistentMemorySystem
from monitoring_system import MonitoringSystem
from rag.service import RagService, IngestionOptions, QueryOptions

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_env_name() -> str:
    return os.getenv("AI_DEVOPS_ENV", os.getenv("ENVIRONMENT", "production")).lower()


def _parse_allowed_origins() -> List[str]:
    raw = os.getenv("AI_DEVOPS_ALLOWED_ORIGINS", "").strip()
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]


def _collect_api_keys() -> List[str]:
    keys: List[str] = []
    for name in ("AI_DEVOPS_API_KEY", "BRAINOPS_API_KEY", "ADMIN_API_KEY"):
        value = os.getenv(name, "").strip()
        if value:
            keys.append(value)
    extra_keys = os.getenv("API_KEYS", "")
    if extra_keys:
        keys.extend([k.strip() for k in extra_keys.split(",") if k.strip()])
    return list(dict.fromkeys(keys))


def _extract_api_key(request: Request) -> Optional[str]:
    header_key = request.headers.get("x-api-key")
    if header_key:
        return header_key.strip()
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return None


def require_api_key(request: Request) -> None:
    allow_unauth = os.getenv("AI_DEVOPS_ALLOW_UNAUTH", "false").lower() in ("1", "true", "yes")
    if allow_unauth and _get_env_name() != "production":
        return

    valid_keys = _collect_api_keys()
    if not valid_keys:
        raise HTTPException(status_code=503, detail="AI DevOps API key not configured")

    token = _extract_api_key(request)
    if not token or token not in valid_keys:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _resolve_rag_paths(paths: List[str]) -> List[str]:
    base_root = Path(os.getenv("AI_DEVOPS_RAG_ROOT", str(Path.cwd()))).resolve()
    resolved: List[str] = []
    for raw_path in paths:
        path_obj = Path(raw_path)
        candidate = (base_root / path_obj).resolve() if not path_obj.is_absolute() else path_obj.resolve()
        if candidate != base_root and base_root not in candidate.parents:
            raise HTTPException(status_code=400, detail="RAG path outside allowed root")
        resolved.append(str(candidate))
    return resolved

# Pydantic models for API
class MemoryRequest(BaseModel):
    content: str
    source: str = "api"
    tags: List[str] = []
    importance: Optional[float] = None
    metadata: Dict[str, Any] = {}

class QueryRequest(BaseModel):
    query: str
    n_results: int = 5

class ConversationRequest(BaseModel):
    human_input: str
    ai_response: str
    metadata: Dict[str, Any] = {}

class HealthCheckResponse(BaseModel):
    status: str
    timestamp: str
    details: Dict[str, Any]

class RagIngestRequest(BaseModel):
    paths: Optional[List[str]] = None
    glob_patterns: Optional[List[str]] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    collection_name: str = "local_docs"
    batch_size: Optional[int] = None
    reset: bool = False
    max_files: Optional[int] = None

class RagQueryRequest(BaseModel):
    query: str
    n_results: int = 5
    provider: Optional[str] = None
    model_name: Optional[str] = None
    collection_name: str = "local_docs"

class ChatRequest(BaseModel):
    message: str
    use_memory: bool = True
    use_rag: bool = True
    rag_results: int = 3
    rag_provider: Optional[str] = None
    rag_model_name: Optional[str] = None
    rag_collection: str = "local_docs"

class AIDevOpsOrchestrator:
    """Main orchestrator for the AI DevOps system"""
    
    def __init__(self):
        self.app = FastAPI(
            title="AI DevOps System",
            description="Ultimate AI-powered DevOps automation system",
            version="1.0.0",
            dependencies=[Depends(require_api_key)],
        )
        
        # Setup CORS
        allowed_origins = _parse_allowed_origins()
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "X-API-Key"],
        )
        
        # Initialize components
        self.memory_system = None
        self.monitoring_system = None
        self.rag_service: Optional[RagService] = None
        self._is_running = False
        
        # Setup API routes
        self._setup_routes()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self._is_running = False
    
    async def initialize(self):
        """Initialize all system components"""
        logger.info("Initializing AI DevOps System...")
        
        try:
            # Initialize memory system
            self.memory_system = PersistentMemorySystem()
            logger.info("Memory system initialized")
            
            # Initialize monitoring system
            self.monitoring_system = MonitoringSystem()
            logger.info("Monitoring system initialized")
            
            # Start monitoring in background
            asyncio.create_task(self._run_monitoring())
            
            self._is_running = True
            logger.info("AI DevOps System fully initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            raise
    
    async def _run_monitoring(self):
        """Run monitoring system in background"""
        try:
            await self.monitoring_system.start_monitoring()
        except Exception as e:
            logger.error(f"Monitoring system error: {e}")

    def _ensure_rag_service(self) -> RagService:
        """Lazily initialize the RagService."""
        if self.rag_service is None:
            self.rag_service = RagService()
        return self.rag_service
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.on_event("startup")
        async def startup_event():
            await self.initialize()
        
        @self.app.on_event("shutdown") 
        async def shutdown_event():
            logger.info("Shutting down AI DevOps System...")
            self._is_running = False
        
        @self.app.get("/", response_model=Dict[str, Any])
        async def root():
            """Root endpoint with system information"""
            return {
                "system": "AI DevOps Orchestrator",
                "version": "1.0.0",
                "status": "running" if self._is_running else "initializing",
                "timestamp": datetime.now().isoformat(),
                "endpoints": {
                    "health": "/health",
                    "memory": "/memory/*",
                    "monitoring": "/monitoring/*",
                    "system": "/system/*"
                }
            }
        
        # Health check endpoints
        @self.app.get("/health", response_model=HealthCheckResponse)
        async def health_check():
            """System health check"""
            try:
                status = self.monitoring_system.get_system_status() if self.monitoring_system else {}
                
                return HealthCheckResponse(
                    status="healthy" if status.get('overall_status') == 'healthy' else "degraded",
                    timestamp=datetime.now().isoformat(),
                    details=status
                )
            except Exception as e:
                logger.error(f"Health check error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Memory system endpoints
        @self.app.post("/memory/store")
        async def store_memory(request: MemoryRequest):
            """Store a memory in the system"""
            try:
                memory_id = self.memory_system.store_memory(
                    content=request.content,
                    source=request.source,
                    tags=request.tags,
                    importance=request.importance,
                    metadata=request.metadata
                )
                return {"memory_id": memory_id, "status": "stored"}
            except Exception as e:
                logger.error(f"Memory storage error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/memory/query")
        async def query_memories(request: QueryRequest):
            """Query memories from the system"""
            try:
                results = self.memory_system.retrieve_memories(
                    query=request.query,
                    n_results=request.n_results
                )
                return {"results": results, "count": len(results)}
            except Exception as e:
                logger.error(f"Memory query error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/memory/conversation")
        async def add_conversation(request: ConversationRequest):
            """Add a conversation turn to memory"""
            try:
                self.memory_system.add_conversation_turn(
                    human_input=request.human_input,
                    ai_response=request.ai_response,
                    metadata=request.metadata
                )
                return {"status": "conversation_added"}
            except Exception as e:
                logger.error(f"Conversation storage error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/memory/context")
        async def get_conversation_context(n_messages: int = 10):
            """Get recent conversation context"""
            try:
                context = self.memory_system.get_conversation_context(n_messages)
                return {"context": context}
            except Exception as e:
                logger.error(f"Context retrieval error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/memory/stats")
        async def get_memory_stats():
            """Get memory system statistics"""
            try:
                stats = self.memory_system.get_memory_stats()
                return stats
            except Exception as e:
                logger.error(f"Memory stats error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Monitoring system endpoints
        @self.app.get("/monitoring/status")
        async def get_monitoring_status():
            """Get detailed monitoring status"""
            try:
                status = self.monitoring_system.get_system_status()
                return status
            except Exception as e:
                logger.error(f"Monitoring status error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/monitoring/alerts")
        async def get_active_alerts():
            """Get active system alerts"""
            try:
                alerts = self.monitoring_system.alert_manager.get_active_alerts()
                return {"alerts": alerts, "count": len(alerts)}
            except Exception as e:
                logger.error(f"Alerts retrieval error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # RAG endpoints
        @self.app.get("/rag/status")
        async def rag_status(collection: str = "local_docs"):
            """Get stats for the configured RAG collection"""
            try:
                service = self._ensure_rag_service()
                return service.get_status(collection)
            except Exception as e:
                logger.error(f"RAG status error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/rag/ingest")
        async def rag_ingest(request: RagIngestRequest):
            """Trigger ingestion into the RAG vector store"""
            try:
                service = self._ensure_rag_service()
                options = IngestionOptions(
                    paths=_resolve_rag_paths(request.paths or ["."]),
                    glob_patterns=request.glob_patterns,
                    chunk_size=request.chunk_size or 1000,
                    chunk_overlap=request.chunk_overlap or 200,
                    provider=request.provider or os.getenv("EMBED_PROVIDER", "sentence-transformers"),
                    model_name=request.model_name or os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2"),
                    collection_name=request.collection_name,
                    batch_size=request.batch_size or 64,
                    reset=request.reset,
                    max_files=request.max_files,
                )
                result = service.ingest(options)
                return result
            except Exception as e:
                logger.error(f"RAG ingest error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/rag/query")
        async def rag_query(request: RagQueryRequest):
            """Query the RAG vector store."""
            try:
                service = self._ensure_rag_service()
                options = QueryOptions(
                    query=request.query,
                    n_results=request.n_results,
                    provider=request.provider,
                    model_name=request.model_name,
                    collection_name=request.collection_name,
                )
                return {"results": service.query(options)}
            except Exception as e:
                logger.error(f"RAG query error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/monitoring/alert/{alert_id}/resolve")
        async def resolve_alert(alert_id: str):
            """Resolve a specific alert"""
            try:
                self.monitoring_system.alert_manager.resolve_alert(alert_id)
                return {"status": "alert_resolved", "alert_id": alert_id}
            except Exception as e:
                logger.error(f"Alert resolution error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # System management endpoints
        @self.app.post("/system/healing/{action}")
        async def perform_healing_action(action: str, background_tasks: BackgroundTasks):
            """Perform a system healing action"""
            try:
                # Run healing action in background
                background_tasks.add_task(
                    self.monitoring_system.auto_healer.perform_healing_action,
                    action
                )
                return {"status": "healing_action_started", "action": action}
            except Exception as e:
                logger.error(f"Healing action error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/system/services")
        async def get_service_status():
            """Get status of all managed services"""
            try:
                status = self.monitoring_system.get_system_status()
                return status.get('services', {})
            except Exception as e:
                logger.error(f"Service status error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # AI model interaction endpoints
        @self.app.post("/ai/chat")
        async def chat_with_ai(request: ChatRequest):
            """Chat with AI using memory + RAG context"""
            try:
                return await self._process_ai_chat(request)
            except Exception as e:
                logger.error(f"AI chat error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Utility endpoints
        @self.app.get("/system/info")
        async def get_system_info():
            """Get comprehensive system information"""
            try:
                info = {
                    "system": "AI DevOps Orchestrator",
                    "version": "1.0.0",
                    "status": "running" if self._is_running else "stopped",
                    "timestamp": datetime.now().isoformat(),
                    "components": {
                        "memory_system": self.memory_system is not None,
                        "monitoring_system": self.monitoring_system is not None,
                    },
                    "environment": {
                        "python_version": sys.version,
                        "working_directory": str(Path.cwd()),
                    }
                }
                
                if self.monitoring_system:
                    info["monitoring"] = self.monitoring_system.get_system_status()
                
                if self.memory_system:
                    info["memory"] = self.memory_system.get_memory_stats()
                
                return info
            except Exception as e:
                logger.error(f"System info error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _process_ai_chat(self, request: ChatRequest) -> Dict[str, Any]:
        """Process chat using both memory context and RAG retrieval."""
        message = request.message
        try:
            memory_context = ""
            relevant_memories: List[Dict[str, Any]] = []
            if request.use_memory and self.memory_system:
                relevant_memories = self.memory_system.retrieve_memories(message, n_results=3)
                conversation_log = self.memory_system.get_conversation_context(n_messages=5)
                memory_snippets = "\n".join(
                    f"- {mem['content'][:200]}..." for mem in relevant_memories
                )
                if memory_snippets.strip():
                    memory_context = f"Conversation Context:\n{conversation_log}\n\nRelevant Memories:\n{memory_snippets}"

            rag_chunks: List[Dict[str, Any]] = []
            rag_context_text = ""
            if request.use_rag:
                rag_service = self._ensure_rag_service()
                rag_chunks = rag_service.query(
                    QueryOptions(
                        query=message,
                        n_results=request.rag_results,
                        provider=request.rag_provider,
                        model_name=request.rag_model_name,
                        collection_name=request.rag_collection,
                    )
                )
                if rag_chunks:
                    rag_context_lines = [
                        f"- ({chunk.get('similarity', 0):.2f}) {str(chunk.get('content', ''))[:200]}..."
                        for chunk in rag_chunks
                    ]
                    rag_context_text = "Relevant Knowledge:\n" + "\n".join(rag_context_lines)

            response = f"I received your message: '{message}'"
            if memory_context:
                response += "\n\n" + memory_context
            if rag_context_text:
                response += "\n\n" + rag_context_text

            if request.use_memory and self.memory_system:
                self.memory_system.add_conversation_turn(
                    human_input=message,
                    ai_response=response,
                    metadata={
                        "relevant_memories_count": len(relevant_memories),
                        "rag_chunks": len(rag_chunks),
                    },
                )

            return {
                "response": response,
                "memory_context": memory_context,
                "rag_chunks": rag_chunks,
            }

        except Exception as e:
            logger.error(f"AI chat processing error: {e}")
            return {
                "response": f"Sorry, I encountered an error processing your message: {str(e)}"
            }
    
    def run_server(self, host: str = "0.0.0.0", port: int = 8080, reload: bool = False):
        """Run the FastAPI server"""
        logger.info(f"Starting AI DevOps Orchestrator on {host}:{port}")
        
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        return server.run()

# CLI interface
def main():
    parser = argparse.ArgumentParser(description="AI DevOps Orchestrator")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--mode", choices=["server", "status", "test"], default="server", help="Run mode")
    
    args = parser.parse_args()
    
    if args.mode == "status":
        # Quick status check
        orchestrator = AIDevOpsOrchestrator()
        print("AI DevOps System Status Check")
        print("=" * 40)
        # Would implement status checking here
        print("System: Not yet initialized (run in server mode)")
        
    elif args.mode == "test":
        # Test mode
        async def test_system():
            orchestrator = AIDevOpsOrchestrator()
            await orchestrator.initialize()
            
            # Test memory system
            memory_id = orchestrator.memory_system.store_memory(
                "Test memory entry",
                source="test",
                tags=["test"]
            )
            print(f"Stored test memory: {memory_id}")
            
            # Test memory retrieval
            results = orchestrator.memory_system.retrieve_memories("test")
            print(f"Retrieved {len(results)} memories")
            
            # Test system status
            if orchestrator.monitoring_system:
                status = orchestrator.monitoring_system.get_system_status()
                print(f"System status: {status['overall_status']}")
            
            print("Test completed successfully!")
        
        asyncio.run(test_system())
        
    else:
        # Server mode (default)
        orchestrator = AIDevOpsOrchestrator()
        orchestrator.run_server(
            host=args.host,
            port=args.port,
            reload=args.reload
        )

if __name__ == "__main__":
    main()
