#!/usr/bin/env python3
"""
Fix v9.17 deployment by ensuring clean build
"""

import subprocess
import time
import os

def run_command(cmd, description):
    """Run command and show output"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"⚠️ Stderr: {result.stderr}")
    return result.returncode == 0

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║                   v9.17 DEPLOYMENT FIX                      ║
║                                                            ║
║  Fixing deployment issues with clean build                 ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # 1. Update version
    print("\n1️⃣ Updating version to 9.17...")
    with open("main.py", "r") as f:
        content = f.read()
    
    # Update version string
    content = content.replace('"version": "9.16"', '"version": "9.17"')
    content = content.replace('"version": "9.15"', '"version": "9.17"')
    content = content.replace('"version": "9.14"', '"version": "9.17"')
    
    with open("main.py", "w") as f:
        f.write(content)
    
    print("✅ Version updated to 9.17")
    
    # 2. Clean Docker build
    print("\n2️⃣ Building Docker image v9.17...")
    
    # Login to Docker Hub first
    run_command(
        "DOCKER_CONFIG=/tmp/.docker docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'",
        "Docker Hub login"
    )
    
    # Clean build
    success = run_command(
        "DOCKER_CONFIG=/tmp/.docker docker build -t mwwoodworth/brainops-backend:v9.17 -f Dockerfile . --no-cache",
        "Building v9.17 (clean build)"
    )
    
    if not success:
        print("❌ Build failed! Checking Dockerfile...")
        # Try simpler Dockerfile
        with open("Dockerfile.simple", "w") as f:
            f.write("""FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 10000

# Start command
CMD ["python", "main.py"]
""")
        
        # Try with simple Dockerfile
        success = run_command(
            "DOCKER_CONFIG=/tmp/.docker docker build -t mwwoodworth/brainops-backend:v9.17 -f Dockerfile.simple .",
            "Building v9.17 with simple Dockerfile"
        )
    
    if not success:
        print("❌ Build still failing. Exiting.")
        return
    
    # 3. Tag as latest
    run_command(
        "DOCKER_CONFIG=/tmp/.docker docker tag mwwoodworth/brainops-backend:v9.17 mwwoodworth/brainops-backend:latest",
        "Tagging as latest"
    )
    
    # 4. Push to Docker Hub
    print("\n3️⃣ Pushing to Docker Hub...")
    success = run_command(
        "DOCKER_CONFIG=/tmp/.docker docker push mwwoodworth/brainops-backend:v9.17",
        "Pushing v9.17"
    )
    
    if success:
        run_command(
            "DOCKER_CONFIG=/tmp/.docker docker push mwwoodworth/brainops-backend:latest",
            "Pushing latest"
        )
    
    # 5. Trigger deployment
    print("\n4️⃣ Triggering Render deployment...")
    run_command(
        'curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM"',
        "Deploy hook trigger"
    )
    
    print("""
╔════════════════════════════════════════════════════════════╗
║                    DEPLOYMENT INITIATED                     ║
║                                                            ║
║  Version: v9.17                                           ║
║  Status: Building and pushing...                          ║
║  Note: Neural OS completely removed                       ║
║                                                            ║
║  Monitor at:                                              ║
║  https://dashboard.render.com/web/srv-d1tfs4idbo4c73di6k00║
╚════════════════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    main()