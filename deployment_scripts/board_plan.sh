# Systems Integration Script
# Frontend: myroofgenius-app
cd ~/code/myroofgenius-app
npm install @copilotkit/react-core @copilotkit/react-ui framer-motion
npm install --save-dev @types/node

# Backend: fastapi-operator-env
cd ~/code/fastapi-operator-env
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
        yield {
            "event": "update",
            "data": json.dumps({"step": i+1, "message": f"Processing step {i+1}/5"})
        }
        await asyncio.sleep(1)

@app.get("/orchestrate/stream")
async def stream_orchestration():
    return EventSourceResponse(event_generator())
EOF

# Start services
cd ~/code/myroofgenius-app
npm run dev -- --port 3000 &

cd ~/code/fastapi-operator-env
source .venv/bin/activate
uvicorn orchestrator:app --reload --port 9000 &

