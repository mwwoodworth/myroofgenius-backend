from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

app = FastAPI(title="BrainOps AI Board API")

# In-memory stores
agents = {}
memory = {}
orchestration_logs = []

class Agent(BaseModel):
    name: str
    role: str
    capabilities: List[str]
    callback_url: Optional[str] = None

class MemorySeed(BaseModel):
    labels: List[str]
    items: List[Dict[str, str]]

class OrchestrationRequest(BaseModel):
    objective: str
    inputs: Dict[str, Any]
    agents: List[Dict[str, str]]
    outputs: List[str]

@app.get("/health")
async def health():
    return {"ok": True, "timestamp": datetime.now().isoformat()}

@app.post("/agents/register")
async def register_agent(agent: Agent):
    if agent.name in agents:
        return {"exists": True, "agent": agent.name}
    agents[agent.name] = agent.dict()
    return {"created": True, "agent": agent.name}

@app.post("/memory/seed")
async def seed_memory(seed: MemorySeed):
    count = 0
    for item in seed.items:
        key = item.get("key")
        if key:
            memory[key] = {"value": item.get("value"), "labels": seed.labels}
            count += 1
    return {"ok": True, "upserted": count}

@app.post("/orchestrate")
async def orchestrate(request: OrchestrationRequest):
    # Extract frontend/backend info from inputs if available
    fe_info = request.inputs.get("frontend", {})
    be_info = request.inputs.get("backend", {})
    ports = request.inputs.get("ports", {"fe": 3000, "be": 9000})
    
    bash_cmds = f"""# Systems Integration Script
# Frontend: {fe_info.get('name', 'myroofgenius-app')}
cd {fe_info.get('path', '~/code/myroofgenius-app')}
npm install @copilotkit/react-core @copilotkit/react-ui framer-motion
npm install --save-dev @types/node

# Backend: {be_info.get('name', 'fastapi-operator-env')}
cd {be_info.get('path', '~/code/fastapi-operator-env')}
uv venv || true
source .venv/bin/activate
echo 'fastapi[all]
uvicorn
pgvector
sqlalchemy
httpx
sse-starlette' > requirements.txt
uv pip install -r requirements.txt

# Create streaming orchestrator endpoint
cat > orchestrator.py << 'EOF'
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

app = FastAPI()

async def event_generator():
    for i in range(5):
        yield {{
            "event": "update",
            "data": json.dumps({{"step": i+1, "message": f"Processing step {{i+1}}/5"}})
        }}
        await asyncio.sleep(1)

@app.get("/orchestrate/stream")
async def stream_orchestration():
    return EventSourceResponse(event_generator())
EOF

# Start services
cd {fe_info.get('path', '~/code/myroofgenius-app')}
npm run dev -- --port {ports['fe']} &

cd {be_info.get('path', '~/code/fastapi-operator-env')}
source .venv/bin/activate
uvicorn orchestrator:app --reload --port {ports['be']} &
"""
    
    result = {
        "plan": f"AI Board Strategy for: {request.objective}\n1. Gemini: Strategic analysis\n2. Perplexity: Research phase\n3. ChatGPT: Execution planning\n4. Claude: Content creation\n5. NotebookLM: Knowledge capture",
        "task_graph": {
            "phases": ["research", "planning", "implementation", "documentation"],
            "dependencies": {"planning": ["research"], "implementation": ["planning"], "documentation": ["implementation"]}
        },
        "bash_commands": bash_cmds,
        "api_specs": {
            "endpoints": ["/ai/stream", "/health", "/vectors/search", "/orchestrate/stream"],
            "streaming": "SSE with async generators",
            "database": "PostgreSQL with pgvector extension"
        },
        "integration_report": {
            "frontend": fe_info,
            "backend": be_info,
            "ports": ports,
            "status": "Ready for integration"
        },
        "summary": "Orchestration complete",
        "acceptance": request.inputs.get("acceptance", [])
    }
    orchestration_logs.append(result)
    return result

@app.get("/logs/recent")
async def get_recent_logs():
    if orchestration_logs:
        return orchestration_logs[-1]
    return {"message": "No orchestration logs yet"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
