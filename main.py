"""
Minimal BrainOps Backend to Test Render Deployment
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Initialize FastAPI
app = FastAPI(title="BrainOps AI Orchestration", version="1.0.0")

# CORS for frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://myroofgenius.com", "https://weathercraft-erp.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "BrainOps AI Orchestration Backend", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "brainops-backend"}

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/readyz")
async def readyz():
    return {"status": "ready"}

@app.get("/livez")
async def livez():
    return {"status": "live"}

@app.get("/metrics")
async def metrics():
    return {
        "service": "brainops-backend",
        "uptime": "healthy",
        "requests": 0,
        "errors": 0
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))